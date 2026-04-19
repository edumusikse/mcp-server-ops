import * as vscode from 'vscode';
import { OpsPanel } from './OpsPanel';
import { FleetPanel } from './FleetPanel';
import { McpClient } from './McpClient';

/**
 * Shared MCP client between Chat and Fleet panels.
 * Lazy-connects on first use; reconnects if the SSH subprocess dies.
 */
class SharedMcp {
    private client?: McpClient;
    private connecting?: Promise<McpClient>;

    async get(): Promise<McpClient> {
        if (this.client) return this.client;
        if (this.connecting) return this.connecting;

        const cfg = vscode.workspace.getConfiguration('ops-panel');
        const host       = cfg.get<string>('sshHost', 'onyx');
        const python     = cfg.get<string>('pythonPath', '/opt/ops-mcp/.venv/bin/python3');
        const serverPath = cfg.get<string>('mcpServerPath', '/opt/ops-mcp/server.py');

        const next = new McpClient(host, python, serverPath);
        this.connecting = next.connect().then(() => {
            this.client = next;
            this.connecting = undefined;
            return next;
        }).catch((e) => {
            this.connecting = undefined;
            throw e;
        });
        return this.connecting;
    }

    reset() {
        this.client?.disconnect();
        this.client = undefined;
        this.connecting = undefined;
    }
}

export function activate(ctx: vscode.ExtensionContext) {
    const shared = new SharedMcp();

    ctx.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            OpsPanel.viewId,
            new OpsPanel(ctx, () => shared.get()),
            { webviewOptions: { retainContextWhenHidden: true } },
        ),
        vscode.window.registerWebviewViewProvider(
            FleetPanel.viewId,
            new FleetPanel(ctx, () => shared.get()),
            { webviewOptions: { retainContextWhenHidden: true } },
        ),
    );
}

export function deactivate() {}
