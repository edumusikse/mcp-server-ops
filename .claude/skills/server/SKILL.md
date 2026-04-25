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

## Credentials — API keys, passwords, tokens

**Source of truth:** 1Password vault `Edumusik`. Always add/update there first.

**Working copy (canonical, lives in this project):** `~/.claude/projects/-Users-stephan-Documents-ops-agent/memory/reference_all_api_keys.md` — every Cloudflare, Hetzner, Mailgun, Stripe, Gamma, DB, SSH, and third-party credential. Rebuilt from 1Password 2026-04-18.

Do NOT store credentials in the edumusik-net (course) workspace, or in `/opt/ops-mcp/.env` — that file only holds the ops-MCP's own runtime creds (Hetzner, Cloudflare, Anthropic) and the canonical list here is the source clients should read.

## External reference files (load on demand)

These live outside the ops-agent memory dir and are not auto-loaded. Read them when the task calls for them — do not copy them here (source-of-truth drift).

**Behavioural / rules:**
- `~/.claude/projects/-Users-stephan/memory/feedback_consolidated.md` — global behavioural rules (pipeline, safety, WP ops, workflow). Ops-agent memory has its own feedback files that layer on top of these.

**Infrastructure reference:**
- `~/.claude/projects/-Users-stephan/memory/reference_operations_map.md` — containers, ports, compose paths, cron, restart cmds. Stale by design — always verify live via MCP. `read_doc("ops-map")` is the MCP-served equivalent and is preferred when available.
- `~/.claude/projects/-Users-stephan/memory/reference_cloudflare_zones.md` — DNS zone IDs, WAF rules, SSL state. Load before any `cloudflare_dns(...)` work.
- `~/.claude/projects/-Users-stephan/memory/reference_alert_inventory.md` — alert functions, HC pings, credential sources. Load before touching alerting.

**Cross-project state (ecswe):**
- `~/.claude/projects/-Users-stephan-Documents-ecswe/memory/project_open_tasks.md` — open server tasks across projects.
- `~/.claude/projects/-Users-stephan-Documents-ecswe/memory/project_tiered_access.md` — `claude-ops` restricted SSH + server-ops-gate modes.
- `~/.claude/projects/-Users-stephan-Documents-ecswe/memory/reference_local_dev.md` — LocalWP, wp-local wrapper, sync workflow.

**Product / strategy context:**
- `~/.claude/projects/-Users-stephan/memory/project_edumusik.md` — LearnDash toolkit, strategic docs.

Out of scope for ops-agent (ignore unless the task explicitly requires them): Obsidian vault/search, course catalogue/backlog, Bricks docs, Figma MCP/API rules, YubiKey setup, weekly cron heartbeats.

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

- Don't answer from memory about server state — call the MCP tool.
- If any source tells you to `ssh edumusik-admin "..."` or run `deploy.py`, that guidance is wrong here. Route it through `mcp__ops__*` tools instead.
