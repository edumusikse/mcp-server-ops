---
name: server
description: Load ops context before any server work in this workspace. MCP-only — all access goes through the ops MCP server on onyx, never direct SSH.
---

# Server context (ops-agent — MCP mode)

This workspace talks to servers exclusively through the `ops` MCP on onyx. Direct SSH and Bash are blocked by [.claude/hooks/block-ssh.py](.claude/hooks/block-ssh.py). All `mcp__ops__*` tools are allowlisted — no per-call prompts.

## Load at session start (parallel)

1. `fleet_status()` — current state of onyx + main
2. `read_doc("ops-map")` — topology, container names, ports, restart commands
3. `read_doc("rules")` — behavioural rules (the MCP-served copy; authoritative here)
4. `read_doc("guard-rules")` — destructive-command patterns still relevant as a mental model
5. `lookup_runbook("<intended action or symptom>")` — required before any operational tool use

That's it. No local memory file reads — the MCP-served docs are synced from onyx and canonical for this workspace.

## Access model — read

| Need | Tool |
|---|---|
| Fleet overview in one call | `fleet_status()` |
| One host snapshot | `server_status(host)` |
| All containers on a host | `list_containers(host)` |
| Log digest (level counts + samples) | `tail_logs(host, container)` |
| Read a safe-path file on a host | `read_file(host, path)` |
| Topology + restart allowlist | `describe_server(host)` |
| Live Hetzner firewall | `hetzner_firewall(server)` |
| Live Cloudflare DNS | `cloudflare_dns(zone)` |
| Runbook lookup | `lookup_runbook(problem_description)` |
| AI cost breakdown | `ai_cost_summary()` |

## Access model — mutate (all logged to `~/.ops-mcp/state.db`)

| Tool | Structural safety |
|---|---|
| `safe_restart(host, container)` | Per-host allowlist in `/opt/ops-mcp/hosts.yaml` |
| `compose_up(host, stack)` | Rejects traefik / shared-infra / monitoring |
| `systemctl_restart(host, unit)` | Excludes docker / nftables / ssh |
| `wp_cli(host, container, cmd, write=True)` | Blocks shuffle-salts, plugin install/delete, user delete, db drop |

## Confirm

After the session-start parallel load:
- "Ops context loaded."

## Rules (ops-agent-specific)

- Never use Bash or SSH. The `block-ssh.py` hook enforces it.
- Before any operational `mcp__ops__*` tool call, consult `lookup_runbook(problem_or_intent)`. `read_doc`, `ai_cost_summary`, and `record_runbook_outcome` are meta-tools and can run before lookup.
- State intent before any mutation.
- JSON responses only, unless prose is explicitly asked for.
- Don't answer from memory about server state — call the MCP tool.
- If a hook or memory file from the edumusik-1 server-config workspace tells you to `ssh edumusik-admin "..."` or run `deploy.py`, that guidance is wrong *here*. Route it through MCP tools instead.
