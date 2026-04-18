# ops-agent

Dedicated Claude Code project for AI-assisted server monitoring of the EduMusik onyx server
(46.225.176.163). All server interaction is through the ops-mcp MCP server — no direct SSH or
Bash commands. The SSH-blocking hook in `.claude/settings.json` enforces this.

## What this project is for

This project exists to demonstrate and operate a token-efficient server monitoring pattern:

1. **MCP server** (`ops-mcp`) runs on onyx and digests raw server output locally before returning it
2. **Structured output** — Claude is prompted for JSON responses, not prose
3. Together these reduce per-call token cost by ~59% vs a full dev session with raw SSH

The benchmark script (`benchmark.py`) proved this with real API calls:

| Approach | Input tokens | Output tokens | Cost/call | Monthly (5-min) |
|----------|-------------|---------------|-----------|-----------------|
| Full dev session (raw SSH + prose) | 2,458 | 365 | $0.0043 | $37.00 |
| ops-agent (MCP digest + JSON) | 1,182 | 118 | $0.0018 | $15.31 |
| **Saving** | **52% fewer** | **68% fewer** | **59% cheaper** | **$21.70/month** |

## MCP tools available

- `mcp__onyx-ops__server_status` — containers, disk %, RAM %, uptime (pre-digested)
- `mcp__onyx-ops__list_containers` — all containers with status and age
- `mcp__onyx-ops__tail_logs` — log digest (not raw lines) — args: container, lines (max 200)
- `mcp__onyx-ops__safe_restart` — restart allowlisted containers only (currently: beszel-agent)
- `mcp__onyx-ops__describe_server` — topology summary with ports
- `mcp__onyx-ops__read_doc` — read server docs: ops-map, rules, or guard-rules

## First thing to do in a new session

Call `mcp__onyx-ops__read_doc` with `name="ops-map"` to load the full service topology
(container names, ports, compose paths). Then `server_status` for current state.

## Rules

- Never use Bash or SSH. The hook will block it. Use MCP tools for everything.
- For server mutations (restart), state what you intend to do and ask before acting.
- Structured JSON responses only — no prose health summaries unless explicitly asked.

## Server docs (on-server at /opt/ops-mcp/docs/, readable via read_doc)

- `ops-map` — container names, ports, compose file paths for all services
- `rules` — operational guardrails and behavioural rules
- `guard-rules` — guard rule patterns (YAML)

## Current project — what we're building and why

The EduMusik server setup grew a complex hook system (guard-ops-harness.py, guard-ssh-writes.sh,
guard-bash.sh, guard-validate.py, etc.) to enforce guardrails on Claude's server access. These
hooks fire on every tool call, add latency, cause permission friction, burn tokens describing
what they blocked, and create constant maintenance overhead. The monthly API cost is ~$200 when
it should be ~$20.

This project is the replacement architecture. The principle: **guardrails belong in the MCP
server, not in hooks**. If `safe_restart` only accepts an allowlist, it's structurally impossible
to restart the wrong container — no hook needed. If `tail_logs` returns a digest, it's
structurally impossible to flood context with raw logs.

**What's been proven** (benchmarked with real API calls, 2026-04-18):
- MCP digest + structured JSON output = 59% cost reduction vs full dev session with raw SSH
- Input tokens: 2,458 → 1,182 (52% fewer)
- Output tokens: 365 → 118 (68% fewer)
- Monthly cost at 5-min health-check cadence: $37 → $15

**What's next:**
1. Extend MCP tools to cover Hetzner API (firewall rules) and Cloudflare DNS — replacing the
   need for hooks that guard those operations
2. Pass credentials (Hetzner API token, Cloudflare token) as env vars in the MCP server launch
   config in `~/.claude.json` — never in context, never on the server in a readable file
3. Add a `run_health_check` tool that returns a single structured JSON verdict — the foundation
   for an always-on monitoring agent callable from anywhere, not just from the Mac

The existing vs-code project and its hooks are untouched — this project is the clean successor.

## MCP server internals (for debugging)

- Source: `/opt/ops-mcp/server.py` and `state.py` on onyx
- Audit log: `/home/stephan/.ops-mcp/state.db` (SQLite)
- Process log: `/home/stephan/.ops-mcp/ops-mcp.log`
- Runtime: stephan user, spawned fresh per Claude Code session via stdio transport
- Registration: `~/.claude.json` → projects → `/Users/stephan/Documents/ops-agent` → mcpServers
