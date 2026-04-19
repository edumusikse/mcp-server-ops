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

| Tool | Description |
|------|-------------|
| `fleet_status()` | All hosts in parallel — one call for a full overview |
| `server_status(host)` | Containers, disk %, RAM %, uptime |
| `list_containers(host)` | All containers with status and age |
| `tail_logs(host, container)` | Log digest — level counts, errors, samples |
| `safe_restart(host, container)` | Restart allowlisted containers only |
| `describe_server(host)` | Topology: containers, ports, allowlist |
| `read_doc(name)` | Read ops docs: ops-map, rules, guard-rules |
| `hetzner_firewall(server)` | Live firewall rules via Hetzner API |
| `cloudflare_dns(zone)` | Live DNS records via Cloudflare API |
| `health_summary(max_age_minutes?)` | Latest synthetic-probe results per host/container/probe |
| `run_health_probes()` | Run all probes now (bypass 15m timer) |

All tools are in `allowedTools` — no per-call permission prompts. Safety is structural: `safe_restart` only accepts containers in the per-host `restart_allowlist`, `compose_up` rejects shared-infra/traefik/monitoring, `systemctl_restart` excludes docker/nftables/ssh, `wp_cli` blocks destructive verbs. All mutations are logged to `~/.ops-mcp/state.db` and surface in the review queue.

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

## Rules

- Never use Bash or SSH — the hook blocks it. Use MCP tools.
- State intent before any mutation (restart). Ask before acting.
- JSON responses only — no prose summaries unless asked.

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
