import { spawn, ChildProcess } from 'child_process';

export interface McpTool {
    name: string;
    description: string;
    inputSchema: Record<string, unknown>;
}

export class McpClient {
    private proc: ChildProcess | null = null;
    private buf = '';
    private pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();
    private nextId = 1;
    private ready = false;
    private host: string;
    private pythonPath: string;
    private serverPath: string;
    public tools: McpTool[] = [];

    constructor(host: string, pythonPath: string, serverPath: string) {
        this.host = host;
        this.pythonPath = pythonPath;
        this.serverPath = serverPath;
    }

    async connect(): Promise<void> {
        if (this.ready) return;

        this.proc = spawn('ssh', [
            '-o', 'ConnectTimeout=10',
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            this.host,
            this.pythonPath,
            this.serverPath,
        ], { stdio: ['pipe', 'pipe', 'pipe'] });

        this.proc.stdout!.on('data', (d: Buffer) => {
            this.buf += d.toString();
            this.flush();
        });

        this.proc.on('exit', () => {
            this.ready = false;
            this.proc = null;
            for (const { reject } of this.pending.values()) {
                reject(new Error('MCP process exited'));
            }
            this.pending.clear();
        });

        await this.rpc('initialize', {
            protocolVersion: '2024-11-05',
            capabilities: {},
            clientInfo: { name: 'ops-panel', version: '0.1.0' },
        });

        this.notify('notifications/initialized');

        const listed = await this.rpc('tools/list', {}) as { tools: McpTool[] };
        this.tools = listed.tools ?? [];
        this.ready = true;
    }

    async callTool(name: string, args: Record<string, unknown> = {}): Promise<string> {
        if (!this.ready) await this.connect();
        const result = await this.rpc('tools/call', { name, arguments: args }) as {
            content: Array<{ type: string; text?: string }>;
        };
        return result.content?.map(c => c.text ?? '').join('\n') ?? '';
    }

    disconnect() {
        this.proc?.stdin?.end();
        this.proc?.kill();
        this.proc = null;
        this.ready = false;
    }

    private flush() {
        const lines = this.buf.split('\n');
        this.buf = lines.pop() ?? '';
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            let msg: { id?: number; result?: unknown; error?: { message: string } };
            try { msg = JSON.parse(trimmed); } catch { continue; }
            if (msg.id !== undefined && this.pending.has(msg.id)) {
                const { resolve, reject } = this.pending.get(msg.id)!;
                this.pending.delete(msg.id);
                if (msg.error) reject(new Error(msg.error.message));
                else resolve(msg.result);
            }
        }
    }

    private rpc(method: string, params: unknown): Promise<unknown> {
        return new Promise((resolve, reject) => {
            const id = this.nextId++;
            this.pending.set(id, { resolve, reject });
            const msg = JSON.stringify({ jsonrpc: '2.0', id, method, params });
            this.proc!.stdin!.write(msg + '\n');
            setTimeout(() => {
                if (this.pending.has(id)) {
                    this.pending.delete(id);
                    reject(new Error(`MCP timeout: ${method}`));
                }
            }, 30_000);
        });
    }

    private notify(method: string) {
        this.proc!.stdin!.write(JSON.stringify({ jsonrpc: '2.0', method }) + '\n');
    }
}
