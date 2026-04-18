import Anthropic from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import OpenAI from 'openai';
import { Mistral } from '@mistralai/mistralai';
import { McpClient, McpTool } from './McpClient';

export interface Message { role: 'user' | 'assistant'; content: string }

export interface RouterCallbacks {
    onText: (chunk: string) => void;
    onToolStart: (name: string, args: Record<string, unknown>) => void;
    onToolEnd: (name: string, result: string) => void;
    onTokens?: (input: number, output: number) => void;
}

const DEEPSEEK_BASE = 'https://api.deepseek.com';

// ── Tool schema converters ────────────────────────────────────────────────────

function toAnthropicTool(t: McpTool): Anthropic.Tool {
    return { name: t.name, description: t.description, input_schema: t.inputSchema as Anthropic.Tool['input_schema'] };
}

function toGeminiTool(tools: McpTool[]) {
    return [{
        functionDeclarations: tools.map(t => ({
            name: t.name,
            description: t.description,
            parameters: (t.inputSchema && Object.keys(t.inputSchema).length > 0)
                ? t.inputSchema
                : { type: 'object', properties: {} },
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
    const system = tools.length
        ? 'You are an ops assistant with live access to a server fleet via MCP tools. You MUST call the provided tools to retrieve real data — never invent, guess, or hallucinate server state, container names, logs, or metrics. If a tool call fails, say so explicitly.'
        : 'You are an ops assistant. MCP tools are not connected — say so and do not invent server data.';

    let totalIn = 0, totalOut = 0;

    while (true) {
        const stream = await client.messages.stream({
            model,
            max_tokens: 2048,
            system,
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
        totalIn += final.usage.input_tokens;
        totalOut += final.usage.output_tokens;
        msgs.push({ role: 'assistant', content: final.content });

        if (final.stop_reason !== 'tool_use') {
            cb.onTokens?.(totalIn, totalOut);
            return assistantText;
        }

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
    const systemInstruction = tools.length
        ? 'You are an ops assistant with live access to a server fleet via MCP tools. You MUST call the provided tools to retrieve real data — never invent, guess, or hallucinate server state, container names, logs, or metrics. If a tool call fails, say so explicitly.'
        : 'You are an ops assistant. MCP tools are not connected — say so and do not invent server data.';
    const gmodel = genai.getGenerativeModel({
        model,
        tools: tools.length ? toGeminiTool(tools) : [],
        systemInstruction,
    });

    const geminiHistory = history.slice(0, -1).map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }],
    }));
    const lastMsg = history[history.length - 1].content;
    const chat = gmodel.startChat({ history: geminiHistory });

    let totalIn = 0, totalOut = 0;
    let userMsg: string | object = lastMsg;

    while (true) {
        const result = await chat.sendMessageStream(userMsg as string);

        let assistantText = '';
        for await (const chunk of result.stream) {
            const text = chunk.text();
            if (text) { assistantText += text; cb.onText(text); }
        }

        const response = await result.response;
        const usage = response.usageMetadata;
        if (usage) {
            totalIn += usage.promptTokenCount ?? 0;
            totalOut += usage.candidatesTokenCount ?? 0;
        }

        const calls = response.functionCalls();
        if (!calls || calls.length === 0) {
            cb.onTokens?.(totalIn, totalOut);
            return assistantText;
        }

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
    const systemMsg = tools.length
        ? 'You are an ops assistant with live access to a server fleet via MCP tools. You MUST call the provided tools to retrieve real data — never invent, guess, or hallucinate server state, container names, logs, or metrics. If a tool call fails, say so explicitly.'
        : 'You are an ops assistant. MCP tools are not connected — say so and do not invent server data.';
    const msgs: OpenAI.Chat.ChatCompletionMessageParam[] = [
        { role: 'system', content: systemMsg },
        ...history.map(m => ({ role: m.role, content: m.content })),
    ];

    let totalIn = 0, totalOut = 0;

    while (true) {
        const usesCompletionTokens = /^(o\d|gpt-5\.)/.test(model);
        const stream = await client.chat.completions.create({
            model,
            messages: msgs,
            tools: tools.length ? tools.map(toOpenAITool) : undefined,
            ...(usesCompletionTokens ? { max_completion_tokens: 2048 } : { max_tokens: 2048 }),
            stream: true,
            stream_options: { include_usage: true },
        });

        let assistantText = '';
        const toolCallsMap = new Map<number, { id: string; name: string; args: string }>();

        for await (const chunk of stream) {
            if (chunk.usage) {
                totalIn += chunk.usage.prompt_tokens;
                totalOut += chunk.usage.completion_tokens;
            }
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

        if (toolCallsMap.size === 0) {
            cb.onTokens?.(totalIn, totalOut);
            return assistantText;
        }

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

// ── Mistral ──────────────────────────────────────────────────────────────────

function toMistralTool(t: McpTool) {
    return {
        type: 'function' as const,
        function: {
            name: t.name,
            description: t.description,
            parameters: (t.inputSchema && Object.keys(t.inputSchema).length > 0)
                ? t.inputSchema
                : { type: 'object', properties: {} },
        },
    };
}

async function runMistral(
    apiKey: string,
    model: string,
    history: Message[],
    tools: McpTool[],
    mcp: McpClient,
    cb: RouterCallbacks,
): Promise<string> {
    const client = new Mistral({ apiKey });
    const systemMsg = tools.length
        ? 'You are an ops assistant with live access to a server fleet via MCP tools. You MUST call the provided tools to retrieve real data — never invent, guess, or hallucinate server state, container names, logs, or metrics. If a tool call fails, say so explicitly.'
        : 'You are an ops assistant. MCP tools are not connected — say so and do not invent server data.';

    const msgs: any[] = [
        { role: 'system', content: systemMsg },
        ...history.map(m => ({ role: m.role, content: m.content })),
    ];

    let totalIn = 0, totalOut = 0;

    while (true) {
        const stream = await client.chat.stream({
            model,
            messages: msgs,
            tools: tools.length ? tools.map(toMistralTool) : undefined,
        });

        let assistantText = '';
        const toolCallsMap = new Map<number, { id: string; name: string; args: string }>();

        for await (const chunk of stream) {
            if (chunk.data.usage) {
                totalIn = chunk.data.usage.promptTokens ?? totalIn;
                totalOut = chunk.data.usage.completionTokens ?? totalOut;
            }
            const delta = chunk.data.choices[0]?.delta;
            if (delta?.content && typeof delta.content === 'string') {
                assistantText += delta.content;
                cb.onText(delta.content);
            }
            for (const tc of delta?.toolCalls ?? []) {
                const idx = tc.index ?? 0;
                if (!toolCallsMap.has(idx)) {
                    toolCallsMap.set(idx, { id: tc.id ?? '', name: tc.function?.name ?? '', args: '' });
                }
                const entry = toolCallsMap.get(idx)!;
                if (tc.id) entry.id = tc.id;
                if (tc.function?.name) entry.name = tc.function.name;
                if (tc.function?.arguments) entry.args += tc.function.arguments;
            }
        }

        if (toolCallsMap.size === 0) {
            cb.onTokens?.(totalIn, totalOut);
            return assistantText;
        }

        msgs.push({
            role: 'assistant',
            content: assistantText || null,
            toolCalls: [...toolCallsMap.values()].map(tc => ({
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
            msgs.push({ role: 'tool', toolCallId: tc.id, content: result });
        }
    }
}

// ── DeepSeek (OpenAI-compatible) ──────────────────────────────────────────────

async function runDeepSeek(
    apiKey: string,
    model: string,
    history: Message[],
    tools: McpTool[],
    mcp: McpClient,
    cb: RouterCallbacks,
): Promise<string> {
    const client = new OpenAI({ apiKey, baseURL: DEEPSEEK_BASE });
    const systemMsg = tools.length
        ? 'You are an ops assistant with live access to a server fleet via MCP tools. You MUST call the provided tools to retrieve real data — never invent, guess, or hallucinate server state, container names, logs, or metrics. If a tool call fails, say so explicitly.'
        : 'You are an ops assistant. MCP tools are not connected — say so and do not invent server data.';
    const msgs: OpenAI.Chat.ChatCompletionMessageParam[] = [
        { role: 'system', content: systemMsg },
        ...history.map(m => ({ role: m.role, content: m.content })),
    ];

    let totalIn = 0, totalOut = 0;

    while (true) {
        const stream = await client.chat.completions.create({
            model,
            messages: msgs,
            tools: tools.length ? tools.map(toOpenAITool) : undefined,
            max_tokens: 2048,
            stream: true,
            stream_options: { include_usage: true },
        });

        let assistantText = '';
        const toolCallsMap = new Map<number, { id: string; name: string; args: string }>();

        for await (const chunk of stream) {
            if (chunk.usage) {
                totalIn += chunk.usage.prompt_tokens;
                totalOut += chunk.usage.completion_tokens;
            }
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

        if (toolCallsMap.size === 0) {
            cb.onTokens?.(totalIn, totalOut);
            return assistantText;
        }

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
    apiKeys: { anthropic?: string; gemini?: string; openai?: string; mistral?: string; deepseek?: string },
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
    if (model.startsWith('gpt-') || model.startsWith('o1') || model.startsWith('o3') || model.startsWith('o4')) {
        if (!apiKeys.openai) throw new Error('OpenAI API key not configured');
        return runOpenAI(apiKeys.openai, model, history, tools, mcp, cb);
    }
    if (model.startsWith('mistral-') || model.startsWith('codestral')) {
        if (!apiKeys.mistral) throw new Error('Mistral API key not configured');
        return runMistral(apiKeys.mistral, model, history, tools, mcp, cb);
    }
    if (model.startsWith('deepseek-')) {
        if (!apiKeys.deepseek) throw new Error('DeepSeek API key not configured');
        return runDeepSeek(apiKeys.deepseek, model, history, tools, mcp, cb);
    }
    throw new Error(`Unknown model prefix: ${model}`);
}
