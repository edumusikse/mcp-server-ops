import * as vscode from 'vscode';
import { McpClient } from './McpClient';

/**
 * Fleet panel: read-only overview (containers + probe health) with
 * per-container restart buttons. Restart is gated server-side by
 * safe_restart's per-host restart_allowlist — the UI only reflects that gate.
 */
export class FleetPanel implements vscode.WebviewViewProvider {
    public static readonly viewId = 'ops-panel.fleet';

    private view?: vscode.WebviewView;
    private mcp?: McpClient;
    private refreshInterval?: NodeJS.Timeout;

    constructor(
        private readonly ctx: vscode.ExtensionContext,
        private readonly getMcp: () => Promise<McpClient>,
    ) {}

    resolveWebviewView(view: vscode.WebviewView) {
        this.view = view;
        view.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(this.ctx.extensionUri, 'media')],
        };
        view.webview.html = this.buildHtml(view.webview);

        view.webview.onDidReceiveMessage(async (msg) => {
            switch (msg.type) {
                case 'ready':          await this.refresh(); break;
                case 'refresh':        await this.refresh(); break;
                case 'runProbes':      await this.runProbes(); break;
                case 'restartContainer': await this.restartContainer(msg.host, msg.container); break;
            }
        });

        // Auto-refresh every 30s while panel is visible
        view.onDidChangeVisibility(() => {
            if (view.visible) this.startAutoRefresh();
            else this.stopAutoRefresh();
        });
        this.startAutoRefresh();
    }

    private startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => this.refresh().catch(() => {}), 30_000);
    }

    private stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = undefined;
        }
    }

    private send(msg: object) {
        this.view?.webview.postMessage(msg);
    }

    private async ensureMcp(): Promise<McpClient> {
        if (!this.mcp) {
            try { this.mcp = await this.getMcp(); }
            catch (e) {
                this.send({ type: 'status', connected: false, error: String(e) });
                throw e;
            }
        }
        return this.mcp;
    }

    private async refresh() {
        try {
            const mcp = await this.ensureMcp();
            const fleet = JSON.parse(await mcp.callTool('fleet_status', {}));
            this.send({ type: 'status', connected: true });
            this.send({ type: 'fleet', data: fleet, ts: Date.now() });
        } catch (e) {
            this.send({ type: 'status', connected: false, error: String(e) });
        }
    }

    private async runProbes() {
        try {
            this.send({ type: 'probesRunning' });
            const mcp = await this.ensureMcp();
            // MCP tool may not exist on older server; fall back to "not available"
            try {
                const raw = await mcp.callTool('run_health_probes', {});
                this.send({ type: 'probesDone', data: JSON.parse(raw) });
            } catch {
                this.send({
                    type: 'probesDone',
                    error: 'run_health_probes not available — reconnect MCP to pick it up.',
                });
            }
            await this.refresh();
        } catch (e) {
            this.send({ type: 'probesDone', error: String(e) });
        }
    }

    private async restartContainer(host: string, container: string) {
        try {
            const mcp = await this.ensureMcp();
            this.send({ type: 'restartRunning', host, container });
            const raw = await mcp.callTool('safe_restart', { host, container });
            let result: any;
            try { result = JSON.parse(raw); } catch { result = { ok: false, error: raw }; }
            this.send({ type: 'restartDone', host, container, result });
            // Re-query fleet a beat later so the UI reflects new uptime
            setTimeout(() => this.refresh().catch(() => {}), 2000);
        } catch (e) {
            this.send({ type: 'restartDone', host, container, result: { ok: false, error: String(e) } });
        }
    }

    private buildHtml(webview: vscode.Webview): string {
        const mediaPath = (file: string) =>
            webview.asWebviewUri(vscode.Uri.joinPath(this.ctx.extensionUri, 'media', file));
        const nonce = [...crypto.getRandomValues(new Uint8Array(16))]
            .map(b => b.toString(16).padStart(2, '0')).join('');

        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <link rel="stylesheet" href="${mediaPath('style.css')}">
  <title>Fleet</title>
</head>
<body class="fleet-body">
  <div id="fleet-header">
    <button id="fleet-refresh" title="Refresh">↻</button>
    <button id="fleet-run-probes" title="Run all health probes">▶ probes</button>
    <span id="fleet-updated" class="fleet-updated"></span>
    <div id="fleet-status-dot" class="dot disconnected"></div>
  </div>
  <div id="fleet-body">
    <div class="fleet-empty">Loading…</div>
  </div>
  <div id="fleet-toast" class="fleet-toast hidden"></div>
  <script nonce="${nonce}" src="${mediaPath('fleet.js')}"></script>
</body>
</html>`;
    }
}
