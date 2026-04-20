# ops-agent

Dedicated Claude Code project for AI-assisted fleet management via MCP.
All server interaction goes through the `ops` MCP server — no direct SSH or Bash.

## Architecture

One MCP server runs on the control server (onyx). It manages the whole fleet via SSH
over the private LAN — zero egress cost, sub-millisecond latency between servers.
Any MCP client connects via a single SSH hop to onyx.

```
Client (any device)
  └── ssh onyx → MCP server (Python)
                    ├── local commands     (onyx tools)
                    └── ssh main-private   (main server, 192.168.50.3)
```

## Fleet

| Host | Role | SSH from control |
|------|------|-----------------|
| `onyx` | Control server / Onyx AI Search | local (no hop) |
| `main` | Main server — WordPress, Traefik | `main-private` (192.168.50.3) |

## MCP tools

All per-host tools take a `host` parameter matching a key in `/opt/ops-mcp/hosts.yaml`.

Headline tools (illustrative — **authoritative list is `EXPECTED_TOOLS` in [tests/test_server_imports.py](tests/test_server_imports.py); 19 tools pinned**):

| Tool | Description |
|------|-------------|
| `fleet_status()` | All hosts in parallel — one call for a full overview |
| `server_status(host)` | Containers, disk %, RAM %, uptime |
| `list_containers(host)` | All containers with status and age |
| `tail_logs(host, container)` | Log digest — level counts, errors, samples |
| `safe_restart(host, container)` | Restart allowlisted containers only |
| `describe_server(host)` | Topology: containers, ports, allowlist |
| `read_doc(name)` | Read ops docs: ops-map, rules, guard-rules |
| `lookup_runbook(problem)` | Prior-incident match + suggested fix |
| `hetzner_firewall(server)` | Live firewall rules via Hetzner API |
| `cloudflare_dns(zone)` | Live DNS records via Cloudflare API |
| `wp_cli(host, site, verb, ...)` | WordPress CLI — destructive verbs blocked |
| `compose_up(host, stack)` | Docker compose up — shared-infra/traefik blocked |
| `read_file` / `write_file` | Guarded file I/O on any fleet host |
| `git_sync(host)` / `bootstrap_git(host)` | Deploy path — no more paste-thrash |

Health probes run server-side via `ops-health-probe.timer`; results land in `state.db:health_probes` and surface in `fleet_status.health.worst`. No dedicated MCP read-tool today.

Permissions: tools are in `permissions.allow` (wildcard `mcp__ops__*`) in `.claude/settings.json` — no per-call prompts. **Do not use the legacy `allowedTools` key — it is silently ignored.** Safety is structural: `safe_restart` only accepts containers in the per-host `restart_allowlist`, `compose_up` rejects shared-infra/traefik/monitoring, `systemctl_restart` excludes docker/nftables/ssh, `wp_cli` blocks destructive verbs. All mutations are logged to `~/.ops-mcp/state.db` and surface in the review queue.

## Health probes — business-outcome monitoring

`fleet_status` observes *infrastructure* (containers up, disk OK). Probes observe *outcomes*: is mail actually being delivered, is wp-cron firing, is the backup recent. Deployed after the 2026-04-19 KSM incident in which 2,445 emails silently failed for 2 weeks while the container stayed green.

| Probe | What it verifies |
|-------|------------------|
| `mailgun` | GET /v3/domains/<domain> returns 200 active; catches IP-allowlist blocks |
| `fsmpt_logs` | `wp_fsmpt_email_logs`: failed rows in the last hour (the signal KSM needed) |
| `wp_cron` | ActionScheduler overdue_pending and failed_24h |
| `fluentcrm_queue` | `wp_fc_campaign_emails`: scheduled due / processing stuck |
| `smtp_auth` | For non-Mailgun sites: SMTP tcp connect + AUTH LOGIN |
| `ssl_dns` | TLS cert days_until_expiry + SPF + DMARC present |
| `backup` | Newest UpdraftPlus/BackWPup/ai1wm backup mtime |
| `stripe_webhook` | WooCommerce orders with `_stripe_charge_id` meta (webhook closing loops) |

Each probe self-discovers (skips WP sites without the plugin). Runs every 15 min via `ops-health-probe.timer` on onyx; results in `state.db:health_probes`. `fleet_status` output includes a per-host `health.worst` summary.

## First thing in a new session

1. `fleet_status()` — current state of all hosts
2. `read_doc("ops-map")` — load service topology
3. `lookup_runbook("<intended action or symptom>")` — consult prior fixes before changing or diagnosing anything operational

## Rules

- **Consult the runbook before any operational action.** Before diagnosis, restart, file read/write, deploy, WP-CLI, DNS/firewall inspection, or other server-facing step, call `lookup_runbook(problem_or_intent)` first. `runbook_compliance.py --ci` flags sessions that skipped it or called it after an operational `mcp__ops__*` tool.
- **Verify before declaring done.** Every claim in a summary, docstring, or commit message must point at the lines that implement it. Covered in `memory/feedback_verify_claims_against_code.md`.
- Never use Bash or SSH — the hook blocks it. Use MCP tools.
- State intent before any mutation (restart). Ask before acting.
- JSON responses only — no prose summaries unless asked.
- Health check: `bash tests/audit.sh` is the single-command workspace health gate — unit tests plus cross-file workspace checks cover hook wiring, guard coverage, docs coherence, deploy invariants, and the runbook mechanism.

## Server layout

`server/` is split into topic modules — `server.py` is a thin entry point that imports each tool module so `@mcp.tool()` decorators register against the shared `mcp` instance from `transport.py`.

| Module | Tools |
|--------|-------|
| `transport.py` | shared `mcp` + FLEET + `run_on` + env bootstrap (no tools) |
| `fleet.py` | `server_status`, `fleet_status`, `list_containers`, `tail_logs`, `safe_restart`, `describe_server`, `systemctl_restart` |
| `wp.py` | `wp_cli` |
| `compose.py` | `compose_up` |
| `files.py` | `read_file`, `write_file` |
| `runbook.py` | `lookup_runbook`, `record_runbook_outcome`, `read_doc`, `ai_cost_summary` |
| `cloud.py` | `hetzner_firewall`, `cloudflare_dns` |
| `deploy.py` | `git_sync`, `bootstrap_git` |
| `guards.py` | `thrash_guard`, `payload_similarity_guard`, runbook hygiene |

## Guards

- **thrash_guard** — 5+ consecutive calls to same `(tool, target)` → stop. Wired into `tail_logs`, `wp_cli`, `read_file`. Test: `python3 tests/test_thrash_guard.py` (6 cases).
- **payload_similarity_guard** — same >=8KB blob through 2 distinct tools (Read→write_file shuttle) → stop, nudge toward `git_sync`. Wired into `read_file`, `write_file`. Test: `python3 tests/test_payload_guard.py` (6 cases).
- **runbook hygiene** — `filter_weak_matches` drops match_score<2 when stronger exists; `flag_runbook_conflicts` clears `auto_executable` on tied-but-disagreeing entries. Test: `python3 tests/test_runbook_hygiene.py` (8 cases).
- **budget_guard** — Claude Code PreToolUse hook (matcher `*`). Session-wide cap: 100k output tokens OR 30 min elapsed (env-override `BUDGET_TOKEN_OUTPUT`, `BUDGET_TIME_MIN`). Warn at 50% via `hookSpecificOutput.additionalContext`, hard-deny at 100% via exit 2. Escape hatches in precedence order: `~/.ops-mcp/budget-off` (presence kill switch, no TTL) > `/tmp/claude-hook-bypass` containing `CONFIRMED` (300s TTL). Lives at `.claude/hooks/budget_guard.py`, wired in `.claude/settings.json`. Test: `python3 tests/test_budget_guard.py` (28 cases).
- **runbook_guard** — Claude Code PreToolUse hook (matcher `mcp__ops__.*`). Pre-enforces what `tests/runbook_compliance.py` detects post-hoc: blocks any operational `mcp__ops__*` tool call if `lookup_runbook` has not yet appeared in the transcript. Exempt tools (callable before lookup): `lookup_runbook`, `read_doc`, `record_runbook_outcome`, `ai_cost_summary` — kept in sync with `RUNBOOK_EXEMPT_TOOLS` in `runbook_compliance.py` and verified by `tests/test_workspace_health.py`. Escape hatches mirror budget_guard: `~/.ops-mcp/runbook-guard-off` (presence kill switch) > `/tmp/claude-hook-bypass` containing `CONFIRMED` (300s TTL). Fail-open on malformed stdin / missing transcript / unhandled exception — never locks a session. Lives at `.claude/hooks/runbook_guard.py`. Test: `python3 tests/test_runbook_guard.py` (38 cases).

## Test harness

- `tests/test_server_imports.py` — pin EXPECTED_TOOLS; fails on dropped `@mcp.tool()`, missing docstring, accidental new tool, or split that doesn't import (4 cases).
- `git_sync` runs a post-sync `import server` against `/opt/ops-mcp/.venv/bin/python3` on the target. If imports break, the call returns `ok: False` with `error: "post_sync_import_failed"` instead of silently leaving the live MCP unimportable. Backup at `<file>.bak.<ts>` is the rollback path.

## Deploy path

No more paste-thrash. Edit locally → commit + push → `git_sync(host)` pulls.
First-time conversion of a non-git `/opt/ops-mcp` uses `bootstrap_git(host)`.
Untracked secrets (`.env`, `hosts.yaml`) survive both flows.

## Compliance harness

`tests/runbook_compliance.py` — static analyzer over Claude transcripts. Detects three anti-patterns per session: `runbook_missed`, `runbook_late` (any operational `mcp__ops__*` tool before `lookup_runbook`), `thrash` (5+ consecutive same tool+target).

- Summarise last 10 sessions: `python3 tests/runbook_compliance.py --pretty`
- CI gate (latest session): `python3 tests/runbook_compliance.py --ci`
- Drift detector (regress = exit 1): `python3 tests/self_audit.py --window 5`
- Deploy parity (static, no network): `python3 tests/live_ops_parity.py --pretty`
- Deploy parity (live, onyx-bash alias): `python3 tests/live_ops_parity.py --live --pretty` — compares tool count, SYNC_FILES, git HEAD, docs on the host; non-strict skip if ssh fails unless `--strict-live`.

## Token benchmark — log analysis, 5 containers (real API calls, 2026-04-18)

| Approach | Input tokens | Output tokens | Cost/call | Monthly (1h) |
|----------|-------------|---------------|-----------|--------------|
| Naive (raw SSH + prose) | 9,171 | 600 | $0.012171 | $8.76 |
| ops-agent (MCP digest + JSON) | 1,418 | 150 | $0.002168 | $1.56 |
| **Saving** | **85% fewer** | **75% fewer** | **82% cheaper** | **$7.20/month** |

## On-server paths (onyx)

- MCP server: `/opt/ops-mcp/server.py`
- Fleet config: `/opt/ops-mcp/hosts.yaml`
- Secrets: `/opt/ops-mcp/.env` (chmod 600)
- Docs: `/opt/ops-mcp/docs/`
- Audit log: `~/.ops-mcp/state.db`
- Process log: `~/.ops-mcp/ops-mcp.log`
