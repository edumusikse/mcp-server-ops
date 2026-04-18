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

`safe_restart` is not in allowedTools — it requires manual approval each time.

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
