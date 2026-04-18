# mcp-server-ops

A token-efficient MCP server that lets your AI coding assistant manage a fleet of Linux servers — without the cost of raw SSH output flooding your context window.

## What it is

This is the **engine** that connects your AI assistant (Claude Code, Cursor, or any MCP-compatible client) to your server fleet. It is not a server management UI — you likely already have Beszel, Grafana, or Portainer for that. This is what makes AI-assisted server operations cheap enough to run continuously.

The MCP server runs on a **control server** inside your infrastructure. It manages all other servers via SSH over your private LAN — zero egress cost between hosts. Your AI client connects via a single SSH hop from anywhere.

```
Your laptop / office / CI
    └── ssh control-server → MCP server (Python)
                                ├── local commands  (control server)
                                ├── ssh 10.0.0.10   (web-01, via LAN)
                                └── ssh 10.0.0.20   (db-01, via LAN)
```

Fleet config lives in one `hosts.yaml` on the control server. Adding a new managed server is one YAML entry — no client changes needed.

---

## The problem

Asking an AI assistant to manage servers via raw SSH output is expensive and slow:

- `docker ps` + `df -h` + `free -m` + `uptime` = ~400 tokens of raw text
- 100 lines of container logs = ~3,200 tokens
- The LLM writes a verbose prose response explaining what it found

Multiply by every health check, every log review, every firewall inspection — costs compound fast.

## The solution

Two levers that stack:

**1. Server-side digestion**
Raw command output is processed on the control server before it reaches the LLM.
`tail_logs` returns `{"errors": 2, "warnings": 5, "sample_info": [...]}` — not 100 raw log lines.

**2. Structured output**
Prompting for `{"ok": bool, "alerts": [...], "action_required": bool}` instead of prose cuts output tokens by ~80%.

## Benchmark (real API calls, claude-haiku-4-5, 2026-04-18)

| | Naive (raw SSH + prose) | This project (MCP digest + JSON) |
|--|--|--|
| Input tokens | 2,458 | 1,182 |
| Output tokens | 365 | 118 |
| Cost/call | $0.0043 | $0.0018 |
| Monthly @ 5-min cadence | $37.00 | $15.31 |
| **Total saving** | — | **59% cheaper** |

For log analysis specifically, the input reduction is ~97%.

---

## MCP tools

| Tool | Description |
|------|-------------|
| `fleet_status()` | All hosts in parallel — one call for a full overview |
| `server_status(host)` | Containers, disk %, RAM %, uptime — pre-digested |
| `list_containers(host)` | All containers with status and age |
| `tail_logs(host, container)` | Log digest: level counts, errors, sample lines |
| `safe_restart(host, container)` | Restart allowlisted containers only |
| `describe_server(host)` | Topology summary with ports |
| `read_doc(name)` | Read ops docs stored on the control server |
| `hetzner_firewall(server)` | Live Hetzner firewall rules via API |
| `cloudflare_dns(zone)` | Live Cloudflare DNS records via API |

Guardrails are structural: `safe_restart` accepts only an explicit per-host allowlist defined in `hosts.yaml`. There is no tool for arbitrary shell execution.

---

## Setup

### 1. Install on the control server

```bash
# On your control server
sudo mkdir -p /opt/ops-mcp
sudo chown $USER /opt/ops-mcp
python3 -m venv /opt/ops-mcp/.venv
/opt/ops-mcp/.venv/bin/pip install mcp fastmcp pyyaml flask

# Copy server files
scp server/server.py server/state.py server/web.py your-control-server:/opt/ops-mcp/
```

### 2. Configure your fleet

Copy `hosts.yaml.example` to `/opt/ops-mcp/hosts.yaml` on the control server and edit it:

```yaml
fleet:
  control:
    ssh: null        # null = local, no SSH hop
    restart_allowlist: []

  web-01:
    ssh: "10.0.0.10" # private LAN IP — no egress cost
    user: ops
    restart_allowlist:
      - nginx
```

### 3. Add secrets

Copy `.env.example` to `/opt/ops-mcp/.env` and fill in your API tokens:

```bash
chmod 600 /opt/ops-mcp/.env
```

Secrets never leave the control server. They are not passed through the MCP channel to the AI client.

### 4. Set up SSH keys

The control server needs passwordless SSH access to each managed host (via private IPs):

```bash
# On the control server
ssh-keygen -t ed25519 -f ~/.ssh/ops-fleet
ssh-copy-id -i ~/.ssh/ops-fleet ops@10.0.0.10
ssh-copy-id -i ~/.ssh/ops-fleet ops@10.0.0.20
```

Add a `~/.ssh/config` entry on the control server for each host alias used in `hosts.yaml`.

### 5. Connect your AI client

**Claude Code:**
```bash
claude mcp add ops --transport stdio -- \
  ssh your-control-server /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/server.py
```

**Any MCP client** — add to your MCP config:
```json
{
  "ops": {
    "type": "stdio",
    "command": "ssh",
    "args": ["your-control-server", "/opt/ops-mcp/.venv/bin/python3", "/opt/ops-mcp/server.py"]
  }
}
```

No API tokens in the client config — secrets stay on the server in `.env`.

### 6. Optional: status dashboard

A lightweight read-only web dashboard shows fleet status and the tool call audit log:

```bash
# On the control server
nohup /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/web.py &
# Access via SSH tunnel: ssh -L 7770:localhost:7770 your-control-server
```

This is an observer, not a management interface — all actual operations go through the MCP tools.

---

## File map

| Path | Purpose |
|------|---------|
| `server/server.py` | MCP server — deploy to control server |
| `server/state.py` | SQLite audit log |
| `server/web.py` | Read-only status dashboard (optional) |
| `hosts.yaml.example` | Fleet config template |
| `.env.example` | Secrets config template |
| `benchmark.py` | Token/cost comparison script |
| `CLAUDE.md` | Claude Code project instructions |
| `.claude/settings.json` | Tool allowlist + SSH-blocking hook |

---

## Extending

Add tools to `server/server.py` using `@mcp.tool()`. Each tool is a guardrail — the AI can only do what the tools expose.

```python
@mcp.tool()
def nginx_config_check(host: str) -> dict:
    """Validate nginx config on a host. Returns ok/errors — not raw output."""
    rc, out = _run_on(host, ["nginx", "-t"])
    return {"ok": rc == 0, "output": out[:500]}
```
