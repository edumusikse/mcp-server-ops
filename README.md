# mcp-server-ops

A token-efficient MCP server for AI-assisted Linux server management.

The MCP server runs on your target server and pre-digests raw command output
before it reaches your LLM. Instead of flooding context with raw `docker ps`,
`free -m`, and log files, it returns compact structured summaries. Guardrails
live in the tool definitions — not in prompt engineering.

Works with any MCP-compatible client: Claude Code, Claude Desktop, Cursor,
or any application built on the MCP protocol.

---

## The problem

Asking an LLM to manage a server via raw SSH output is expensive and slow:

- `docker ps` + `df -h` + `free -m` + `uptime` = ~400 tokens of raw text
- 100 lines of container logs = ~3,200 tokens
- The LLM then writes a verbose prose response explaining what it found

Multiply by every health check, every log review, every firewall inspection —
costs compound fast.

## The solution

Two levers that stack:

**1. Server-side digestion (the MCP server)**
Raw command output is processed on the server before it reaches the LLM.
`tail_logs` returns `{"errors": 2, "warnings": 5, "sample_info": [...]}` —
not 100 raw log lines. The LLM gets signal, not noise.

**2. Structured output**
Prompting for `{"ok": bool, "alerts": [...], "action_required": bool}`
instead of prose cuts output tokens by ~80% and makes responses machine-readable.

## Benchmark (real API calls, claude-haiku-4-5, measured 2026-04-18)

| | Naive (raw SSH + prose) | Optimized (MCP digest + JSON) |
|--|--|--|
| Input tokens | 2,458 | 1,182 |
| Output tokens | 365 | 118 |
| Cost/call | $0.0043 | $0.0018 |
| Monthly @ 5-min cadence | $37.00 | $15.31 |
| **Total saving** | — | **59% cheaper** |

For log analysis specifically, the input reduction is ~97% — 100 raw log lines
become a handful of structured fields.

---

## MCP tools

| Tool | Description |
|------|-------------|
| `server_status` | Containers, disk %, RAM %, uptime — pre-digested |
| `list_containers` | All containers with status and age |
| `tail_logs` | Log digest: level counts, errors, sample lines |
| `safe_restart` | Restart allowlisted containers only |
| `describe_server` | Topology summary with ports |
| `read_doc` | Read ops docs stored on the server |
| `hetzner_firewall` | Live Hetzner firewall rules via API |
| `cloudflare_dns` | Live Cloudflare DNS records via API |

Guardrails are structural: `safe_restart` accepts only an explicit allowlist.
There is no tool for arbitrary shell execution. What the server can't do,
the LLM can't do — no prompt-level enforcement needed.

---

## Setup

### 1. Deploy the MCP server

```bash
# On your server
mkdir -p /opt/ops-mcp
python3 -m venv /opt/ops-mcp/.venv
/opt/ops-mcp/.venv/bin/pip install mcp fastmcp

# Copy server files
scp server/server.py server/state.py your-server:/opt/ops-mcp/
```

### 2. Connect your MCP client

**Claude Code:**
```bash
claude mcp add server-ops --transport stdio -- \
  ssh your-server /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/server.py
```

**Any MCP client** — add to your client's MCP config:
```json
{
  "server-ops": {
    "type": "stdio",
    "command": "ssh",
    "args": ["your-server", "/opt/ops-mcp/.venv/bin/python3", "/opt/ops-mcp/server.py"],
    "env": {
      "HETZNER_API_TOKEN": "optional — for hetzner_firewall tool",
      "CLOUDFLARE_API_TOKEN": "optional — for cloudflare_dns tool"
    }
  }
}
```

API credentials are passed as env vars at spawn time — never stored on the
server, never appear in LLM context.

### 3. Optional: Claude Code project

The `.claude/` directory contains a ready-made Claude Code project:
- `settings.json` — allowlists read-only MCP tools, blocks direct SSH/Docker Bash commands
- `hooks/block-ssh.py` — enforces MCP-only server access
- Copy `CLAUDE.md` and adjust for your server

---

## Benchmark

```bash
export ANTHROPIC_API_KEY=your-key
export SSH_HOST=your-server
python3 benchmark.py
```

Runs two real API calls and prints a full token/cost comparison.

---

## Extending

Add tools to `server/server.py` by decorating functions with `@mcp.tool()`.
Each new tool is a guardrail: the LLM can only do what the tools expose.

```python
@mcp.tool()
def nginx_config_check() -> dict:
    """Validate nginx config. Returns ok/errors — not raw nginx output."""
    rc, out = _run(["nginx", "-t"])
    return {"ok": rc == 0, "output": out[:500]}
```

---

## File map

| Path | Purpose |
|------|---------|
| `server/server.py` | MCP server — deploy to target server |
| `server/state.py` | SQLite audit log and snapshot store |
| `benchmark.py` | Token/cost comparison script |
| `CLAUDE.md` | Claude Code project instructions |
| `.claude/settings.json` | Claude Code tool allowlist + hooks |
| `.claude/hooks/block-ssh.py` | Blocks raw SSH in Claude Code sessions |
