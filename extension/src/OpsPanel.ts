import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { McpClient } from './McpClient';
import { chat, Message } from './router';

const MODELS = [
    { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku (fast)' },
    { id: 'claude-sonnet-4-6',         label: 'Claude Sonnet (balanced)' },
    { id: 'claude-opus-4-7',           label: 'Claude Opus (best)' },
    { id: 'gemini-2.5-pro',             label: 'Gemini 2.5 Pro' },
    { id: 'gemini-2.5-flash',           label: 'Gemini 2.5 Flash (free tier)' },
    { id: 'gpt-5.4',                   label: 'GPT-5.4' },
    { id: 'gpt-5.4-mini',              label: 'GPT-5.4 mini (fast)' },
    { id: 'gpt-4.1',                   label: 'GPT-4.1' },
    { id: 'o3',                        label: 'o3 (reasoning)' },
    { id: 'o4-mini',                   label: 'o4-mini (reasoning, fast)' },
    { id: 'mistral-large-latest',      label: 'Mistral Large (best)' },
    { id: 'mistral-small-latest',      label: 'Mistral Small (fast)' },
    { id: 'codestral-latest',          label: 'Codestral (code)' },
    { id: 'deepseek-chat',             label: 'DeepSeek V3 (chat)' },
    { id: 'deepseek-reasoner',         label: 'DeepSeek R1 (reasoning)' },
];

export class OpsPanel implements vscode.WebviewViewProvider {
    public static readonly viewId = 'ops-panel.chat';

    private view?: vscode.WebviewView;
    private mcp?: McpClient;
    private history: Message[] = [];
    private busy = false;

    constructor(private readonly ctx: vscode.ExtensionContext) {}

    resolveWebviewView(view: vscode.WebviewView) {
        this.view = view;
        view.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(this.ctx.extensionUri, 'media')],
        };
        view.webview.html = this.buildHtml(view.webview);

        view.webview.onDidReceiveMessage(async (msg) => {
            switch (msg.type) {
                case 'send':    await this.handleSend(msg.model, msg.text); break;
                case 'clear':   this.history = []; this.send({ type: 'cleared' }); break;
                case 'ready':   this.sendModels(); this.connectMcp(); break;
            }
        });
    }

    private sendModels() {
        this.send({ type: 'models', models: MODELS });
    }

    private async connectMcp() {
        const cfg = vscode.workspace.getConfiguration('ops-panel');
        const host       = cfg.get<string>('sshHost', 'onyx');
        const python     = cfg.get<string>('pythonPath', '/opt/ops-mcp/.venv/bin/python3');
        const serverPath = cfg.get<string>('mcpServerPath', '/opt/ops-mcp/server.py');

        this.mcp = new McpClient(host, python, serverPath);
        try {
            await this.mcp.connect();
            this.send({ type: 'status', connected: true, toolCount: this.mcp.tools.length });
        } catch (e) {
            this.send({ type: 'status', connected: false, error: String(e) });
        }
    }

    private async handleSend(model: string, text: string) {
        if (this.busy) return;
        this.busy = true;

        if (!this.mcp?.tools) {
            await this.connectMcp();
        }

        this.history.push({ role: 'user', content: text });

        const cfg = vscode.workspace.getConfiguration('ops-panel');
        const apiKeys = {
            anthropic: cfg.get<string>('anthropicApiKey') || process.env.ANTHROPIC_API_KEY,
            gemini:    cfg.get<string>('geminiApiKey')    || process.env.GEMINI_API_KEY,
            openai:    cfg.get<string>('openaiApiKey')    || process.env.OPENAI_API_KEY,
            mistral:   cfg.get<string>('mistralApiKey')   || process.env.MISTRAL_API_KEY,
            deepseek:  cfg.get<string>('deepseekApiKey')  || process.env.DEEPSEEK_API_KEY,
        };

        this.send({ type: 'startAssistant' });

        try {
            let fullText = '';
            const result = await chat(model, apiKeys, this.history, this.mcp!, {
                onText:      (chunk)      => { fullText += chunk; this.send({ type: 'chunk', text: chunk }); },
                onToolStart: (name, args) => this.send({ type: 'toolStart', name, args }),
                onToolEnd:   (name, res)  => this.send({ type: 'toolEnd',   name, result: res }),
                onTokens:    (input, output) => this.send({ type: 'tokens', input, output }),
            });
            this.history.push({ role: 'assistant', content: result });
        } catch (e) {
            this.send({ type: 'error', message: String(e) });
        }

        this.send({ type: 'done' });
        this.busy = false;
    }

    private send(msg: object) {
        this.view?.webview.postMessage(msg);
    }

    private buildHtml(webview: vscode.Webview): string {
        const mediaPath = (file: string) =>
            webview.asWebviewUri(vscode.Uri.joinPath(this.ctx.extensionUri, 'media', file));

        const nonce = [...crypto.getRandomValues(new Uint8Array(16))].map(b => b.toString(16).padStart(2,'0')).join('');

        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="${mediaPath('style.css')}">
  <title>Ops Panel</title>
</head>
<body>
  <div id="header">
    <select id="model-select"></select>
    <button id="clear-btn" title="New session">↺</button>
    <div id="status-dot" class="dot disconnected" title="MCP disconnected"></div>
  </div>
  <div id="messages"></div>
  <div id="input-area">
    <textarea id="input" placeholder="Ask about your fleet…" rows="3"></textarea>
    <button id="send-btn">Send</button>
  </div>
  <script nonce="${nonce}" src="${mediaPath('main.js')}"></script>
</body>
</html>`;
    }
}
