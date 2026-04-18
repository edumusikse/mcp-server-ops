import Anthropic from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import OpenAI from 'openai';
import { McpClient, McpTool } from './McpClient';

export interface Message { role: 'user' | 'assistant'; content: string }

export interface RouterCallbacks {
    onText: (chunk: string) => void;
    onToolStart: (name: string, args: Record<string, unknown>) => void;
    onToolEnd: (name: string, result: string) => void;
}

// ── Tool schema converters ────────────────────────────────────────────────────

function toAnthropicTool(t: McpTool): Anthropic.Tool {
    return { name: t.name, description: t.description, input_schema: t.inputSchema as Anthropic.Tool['input_schema'] };
}

function toGeminiTool(tools: McpTool[]) {
    return [{
        functionDeclarations: tools.map(t => ({
            name: t.name,
            description: t.description,
            parameters: t.inputSchema,
        }))
    }];
}

function toOpenAITool(t: McpTool): OpenAI.Chat.ChatCompletionTool {
    return {
        type: 'function',
        function: { name: t.name, description: t.description, parameters: t.inputSchema },
    };
}

// ── Claude ───────────────────────────────────────────────────────────────────

async function runClaude(
    apiKey: string,
    model: string,
    history: Message[],
    tools: McpTool[],
    mcp: McpClient,
    cb: RouterCallbacks,
): Promise<string> {
    const client = new Anthropic({ apiKey });
    const msgs: Anthropic.MessageParam[] = history.map(m => ({ role: m.role, content: m.content }));

    while (true) {
        const stream = await client.messages.stream({
            model,
            max_tokens: 2048,
            messages: msgs,
            tools: tools.map(toAnthropicTool),
        });

        let assistantText = '';
        for await (const event of stream) {
            if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
                assistantText += event.delta.text;
                cb.onText(event.delta.text);
            }
        }

        const final = await stream.finalMessage();
        msgs.push({ role: 'assistant', content: final.content });

        if (final.stop_reason !== 'tool_use') return assistantText;

        const toolResults: Anthropic.ToolResultBlockParam[] = [];
        for (const block of final.content) {
            if (block.type !== 'tool_use') continue;
            const args = block.input as Record<string, unknown>;
            cb.onToolStart(block.name, args);
            const result = await mcp.callTool(block.name, args);
            cb.onToolEnd(block.name, result);
            toolResults.push({ type: 'tool_result', tool_use_id: block.id, content: result });
        }
        msgs.push({ role: 'user', content: toolResults });
    }
}

// ── Gemini ───────────────────────────────────────────────────────────────────

async function runGemini(
    apiKey: string,
    model: string,
    history: Message[],
    tools: McpTool[],
    mcp: McpClient,
    cb: RouterCallbacks,
): Promise<string> {
    const genai = new GoogleGenerativeAI(apiKey);
    const gmodel = genai.getGenerativeModel({ model, tools: tools.length ? toGeminiTool(tools) : [] });

    const geminiHistory = history.slice(0, -1).map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }],
    }));
    const lastMsg = history[history.length - 1].content;

    const chat = gmodel.startChat({ history: geminiHistory });

    let userMsg: string | object = lastMsg;
    while (true) {
        const result = await chat.sendMessageStream(userMsg as string);

        let assistantText = '';
        for await (const chunk of result.stream) {
            const text = chunk.text();
            if (text) { assistantText += text; cb.onText(text); }
        }

        const response = await result.response;
        const calls = response.functionCalls();
        if (!calls || calls.length === 0) return assistantText;

        const parts = [];
        for (const call of calls) {
            const args = call.args as Record<string, unknown>;
            cb.onToolStart(call.name, args);
            const res = await mcp.callTool(call.name, args);
            cb.onToolEnd(call.name, res);
            parts.push({ functionResponse: { name: call.name, response: { result: res } } });
        }
        userMsg = parts as unknown as string;
    }
}

// ── OpenAI ───────────────────────────────────────────────────────────────────

async function runOpenAI(
    apiKey: string,
    model: string,
    history: Message[],
    tools: McpTool[],
    mcp: McpClient,
    cb: RouterCallbacks,
): Promise<string> {
    const client = new OpenAI({ apiKey });
    const msgs: OpenAI.Chat.ChatCompletionMessageParam[] = history.map(m => ({ role: m.role, content: m.content }));

    while (true) {
        const stream = await client.chat.completions.create({
            model,
            messages: msgs,
            tools: tools.length ? tools.map(toOpenAITool) : undefined,
            stream: true,
        });

        let assistantText = '';
        const toolCallsMap = new Map<number, { id: string; name: string; args: string }>();

        for await (const chunk of stream) {
            const delta = chunk.choices[0]?.delta;
            if (delta?.content) { assistantText += delta.content; cb.onText(delta.content); }
            for (const tc of delta?.tool_calls ?? []) {
                if (!toolCallsMap.has(tc.index)) {
                    toolCallsMap.set(tc.index, { id: tc.id ?? '', name: tc.function?.name ?? '', args: '' });
                }
                const entry = toolCallsMap.get(tc.index)!;
                if (tc.id) entry.id = tc.id;
                if (tc.function?.name) entry.name = tc.function.name;
                if (tc.function?.arguments) entry.args += tc.function.arguments;
            }
        }

        if (toolCallsMap.size === 0) return assistantText;

        msgs.push({
            role: 'assistant',
            content: assistantText || null,
            tool_calls: [...toolCallsMap.values()].map(tc => ({
                id: tc.id,
                type: 'function' as const,
                function: { name: tc.name, arguments: tc.args },
            })),
        });

        for (const tc of toolCallsMap.values()) {
            let args: Record<string, unknown> = {};
            try { args = JSON.parse(tc.args); } catch { /* empty args */ }
            cb.onToolStart(tc.name, args);
            const result = await mcp.callTool(tc.name, args);
            cb.onToolEnd(tc.name, result);
            msgs.push({ role: 'tool', tool_call_id: tc.id, content: result });
        }
    }
}

// ── Public router ─────────────────────────────────────────────────────────────

export async function chat(
    model: string,
    apiKeys: { anthropic?: string; gemini?: string; openai?: string },
    history: Message[],
    mcp: McpClient,
    cb: RouterCallbacks,
): Promise<string> {
    const tools = mcp.tools;

    if (model.startsWith('claude-')) {
        if (!apiKeys.anthropic) throw new Error('Anthropic API key not configured');
        return runClaude(apiKeys.anthropic, model, history, tools, mcp, cb);
    }
    if (model.startsWith('gemini-')) {
        if (!apiKeys.gemini) throw new Error('Gemini API key not configured');
        return runGemini(apiKeys.gemini, model, history, tools, mcp, cb);
    }
    if (model.startsWith('gpt-') || model.startsWith('o1') || model.startsWith('o3')) {
        if (!apiKeys.openai) throw new Error('OpenAI API key not configured');
        return runOpenAI(apiKeys.openai, model, history, tools, mcp, cb);
    }
    throw new Error(`Unknown model prefix: ${model}`);
}
