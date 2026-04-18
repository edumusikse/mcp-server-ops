# ops-agent

A token-efficient Claude Code project for AI-assisted server management via MCP.

## The problem

Using Claude Code for server management in a full development project is expensive:
- The entire project context (CLAUDE.md, skills, memory files) loads into every message
- Raw SSH output — `docker ps`, `free -m`, `df -h` — floods the conversation unprocessed
- Hooks fire on every tool call, adding latency and token overhead
- Result: ~2,500 input tokens and ~400 output tokens per health check interaction

## The solution

Two levers, independently valuable, compounding together:

**1. MCP server-side digestion**
An MCP server runs on the target server and processes raw command output locally before returning it to Claude. Instead of 100 lines of raw logs, Claude receives a structured digest: error count, warning count, 3 unique sample lines. The guardrails live in the tool definitions — `safe_restart` only accepts an allowlist, structurally preventing restarts of unintended containers.

**2. Minimal project context + structured output**
This project has a slim CLAUDE.md (no infrastructure docs, no skills, no memory files) and instructs Claude to respond in structured JSON rather than prose.

## Benchmark results (measured 2026-04-18, claude-haiku-4-5, real API calls)

| | Full dev session | ops-agent |
|--|--|--|
| System prompt | 6,981 chars | 2,845 chars |
| Input tokens | 2,458 | 1,182 |
| Output tokens | 365 | 118 |
| Cost/call | $0.0043 | $0.0018 |
| Monthly @ 5-min cadence | $37.00 | $15.31 |
| **Saving** | — | **59% cheaper** |

For log analysis (`tail_logs`), input token reduction alone is ~97% — 100 raw log lines digest to a handful of structured fields.

## Architecture

```
Claude Code (ops-agent project)
    │
    ├── CLAUDE.md          minimal context, instructs MCP-first
    ├── .claude/
    │   ├── settings.json  allowedTools list, SSH-blocking hook
    │   └── hooks/
    │       └── block-ssh.py   blocks direct SSH/Docker Bash commands
    │
    └── MCP: onyx-ops (stdio over SSH)
            │
            └── /opt/ops-mcp/server.py  (runs on target server)
                    ├── server_status       containers, disk, RAM, uptime
                    ├── list_containers     all containers with age
                    ├── tail_logs           log digest (not raw lines)
                    ├── safe_restart        allowlisted restarts only
                    ├── describe_server     topology with ports
                    ├── read_doc            ops-map, rules, guard-rules
                    ├── hetzner_firewall    live firewall rules via API
                    └── cloudflare_dns      live DNS records via API
```

Credentials for external APIs (Hetzner, Cloudflare) are passed as environment variables in the MCP server launch config — never in Claude's context, never stored on the server.

## Setup

### 1. Deploy the MCP server

Copy `server/` to your target server at `/opt/ops-mcp/`. Create a virtualenv and install dependencies:

```bash
python3 -m venv /opt/ops-mcp/.venv
/opt/ops-mcp/.venv/bin/pip install mcp fastmcp
```

### 2. Register the MCP server in Claude Code

```bash
claude mcp add onyx-ops --transport stdio -- ssh your-server /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/server.py
```

Or add to `~/.claude.json` under `projects` → your project path → `mcpServers`:

```json
{
  "onyx-ops": {
    "type": "stdio",
    "command": "ssh",
    "args": ["your-server", "/opt/ops-mcp/.venv/bin/python3", "/opt/ops-mcp/server.py"],
    "env": {
      "HETZNER_API_TOKEN": "your-token",
      "CLOUDFLARE_API_TOKEN": "your-token"
    }
  }
}
```

### 3. Open the project

```bash
claude /path/to/ops-agent
```

Use the kickoff prompt in `CLAUDE.md` to orient the session.

## Benchmark

Run the benchmark yourself:

```bash
export ANTHROPIC_API_KEY=your-key
export SSH_HOST=your-server   # default: onyx
python3 benchmark.py
```

## File map

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions and current work context |
| `benchmark.py` | Token/cost comparison: full dev session vs ops-agent |
| `.claude/settings.json` | Tool allowlist and SSH-blocking hook |
| `.claude/hooks/block-ssh.py` | Blocks direct SSH/Docker Bash commands |
| `server/` | MCP server source (deploy to target server) |
