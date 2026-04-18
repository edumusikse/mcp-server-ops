#!/usr/bin/env python3
"""
ops-mcp: Fleet control server — one process manages the whole fleet via SSH over LAN.

Runs on the control server. Managed hosts are reached via private network SSH (zero egress cost).
Tools take a `host` parameter; fleet_status() queries all hosts in parallel.

Credentials: /opt/ops-mcp/.env (chmod 600, never in git)
Fleet config: /opt/ops-mcp/hosts.yaml

Transport: stdio
Connect via: ssh control-server /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/server.py

NEVER print to stdout — that is the JSON-RPC transport channel.
"""

import json
import logging
import os
import shlex
import subprocess
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

# ── Bootstrap: load .env before anything else ────────────────────────────────

_ENV_FILE = Path(os.environ.get("OPS_ENV_FILE", "/opt/ops-mcp/.env"))
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Logging (file only — stdout is MCP transport) ────────────────────────────

_LOG_DIR = Path(os.environ.get("OPS_STATE_DIR", str(Path.home() / ".ops-mcp")))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(_LOG_DIR / "ops-mcp.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

sys.path.insert(0, "/opt/ops-mcp")
from state import (  # noqa: E402
    init_db, log_call, save_snapshot,
    get_runbooks, upsert_runbook, update_runbook_outcome,
)

from mcp.server.fastmcp import FastMCP  # noqa: E402

_MCP_NAME = os.environ.get("OPS_MCP_NAME", "ops")
mcp = FastMCP(_MCP_NAME)

# ── Fleet config ──────────────────────────────────────────────────────────────

_HOSTS_FILE = Path(os.environ.get("OPS_HOSTS_FILE", "/opt/ops-mcp/hosts.yaml"))
FLEET: dict = {}
if _HOSTS_FILE.exists():
    _data = yaml.safe_load(_HOSTS_FILE.read_text()) or {}
    FLEET = _data.get("fleet", {})
    logging.info("Fleet loaded: %s", list(FLEET))
else:
    logging.warning("hosts.yaml not found at %s", _HOSTS_FILE)

DOCS_DIR = Path("/opt/ops-mcp/docs")


# ── Command dispatch ──────────────────────────────────────────────────────────

_BANNER_LINES = frozenset([
    "authorised access only. all activity is monitored and logged.",
    "unauthorised access is prohibited and will be prosecuted.",
])


def _strip_banner(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if line.strip().lower() not in _BANNER_LINES
    ).strip()


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Run a command locally."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as e:
        return 1, str(e)


def _run_on(host: str, cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Run a command on a fleet host: local if ssh is null, otherwise via private SSH."""
    cfg = FLEET.get(host)
    if cfg is None:
        return 1, f"Unknown host '{host}'. Known: {list(FLEET)}"

    ssh_addr = cfg.get("ssh")
    if ssh_addr is None:
        return _run(cmd, timeout=timeout)

    user = cfg.get("user", "")
    target = f"{user}@{ssh_addr}" if user else ssh_addr
    ssh_cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no"]
    if cfg.get("identity_file"):
        ssh_cmd += ["-i", cfg["identity_file"]]
    ssh_cmd += [target, shlex.join(cmd)]
    rc, out = _run(ssh_cmd, timeout=timeout + 6)
    return rc, _strip_banner(out)


def _allowlist(host: str) -> set[str]:
    cfg = FLEET.get(host, {})
    items = cfg.get("restart_allowlist", [])
    return {s.strip() for s in items if isinstance(s, str)}


# ── Per-host tools ────────────────────────────────────────────────────────────

@mcp.tool()
def server_status(host: str) -> dict:
    """Pre-digested server state: containers, disk %, RAM %, uptime.

    Args:
        host: Host name from hosts.yaml (e.g. 'onyx', 'main')
    """
    t0 = time.monotonic()

    rc, out = _run_on(host, ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"])
    containers = []
    if rc == 0:
        for line in out.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers.append({"name": parts[0], "status": parts[1]})

    rc, out = _run_on(host, ["df", "-h", "/", "--output=pcent"])
    disk_pct = "?"
    if rc == 0:
        for line in out.splitlines():
            val = line.strip().rstrip("%")
            if val.isdigit():
                disk_pct = val
                break

    rc, out = _run_on(host, ["free", "-m"])
    ram: dict = {}
    for line in out.splitlines():
        if line.startswith("Mem:"):
            p = line.split()
            if len(p) >= 3:
                total, used = int(p[1]), int(p[2])
                ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

    rc, out = _run_on(host, ["uptime", "-p"])
    uptime = "?"
    if rc == 0:
        for line in out.splitlines():
            if line.strip().startswith("up "):
                uptime = line.strip()
                break

    result = {
        "host": host,
        "containers": containers,
        "container_count": len(containers),
        "disk_pct": disk_pct,
        "ram": ram,
        "uptime": uptime,
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("server_status", {"host": host}, result, ms, host=host)
    save_snapshot(result)
    logging.info("server_status %s (%dms)", host, ms)
    return result


@mcp.tool()
def fleet_status() -> dict:
    """Query server_status from all hosts in parallel. One call for a full fleet overview."""
    t0 = time.monotonic()

    def _query(hostname: str):
        try:
            rc, out = _run_on(hostname, ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"])
            containers = []
            if rc == 0:
                for line in out.splitlines():
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        containers.append({"name": parts[0], "status": parts[1]})

            rc, out = _run_on(hostname, ["df", "-h", "/", "--output=pcent"])
            disk_pct = out.splitlines()[-1].strip().rstrip("%") if rc == 0 else "?"

            rc, out = _run_on(hostname, ["free", "-m"])
            ram: dict = {}
            for line in out.splitlines():
                if line.startswith("Mem:"):
                    p = line.split()
                    if len(p) >= 3:
                        total, used = int(p[1]), int(p[2])
                        ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

            rc, out = _run_on(hostname, ["uptime", "-p"])
            return hostname, {
                "containers": containers,
                "container_count": len(containers),
                "disk_pct": disk_pct,
                "ram": ram,
                "uptime": out if rc == 0 else "?",
                "ok": True,
            }
        except Exception as e:
            return hostname, {"ok": False, "error": str(e)}

    results = {}
    with ThreadPoolExecutor(max_workers=max(len(FLEET), 1)) as ex:
        for hostname, result in ex.map(_query, FLEET.keys()):
            results[hostname] = result

    ms = round((time.monotonic() - t0) * 1000)
    response = {"fleet": results, "host_count": len(results)}
    log_call("fleet_status", {}, response, ms)
    logging.info("fleet_status %d hosts (%dms)", len(FLEET), ms)
    return response


@mcp.tool()
def list_containers(host: str) -> list:
    """All Docker containers (running and stopped) with name, status, and age.

    Args:
        host: Host name from hosts.yaml
    """
    t0 = time.monotonic()
    rc, out = _run_on(host, ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.RunningFor}}"])
    containers = []
    if rc == 0:
        for line in out.splitlines():
            p = line.split("\t")
            containers.append({
                "name": p[0] if len(p) > 0 else "",
                "status": p[1] if len(p) > 1 else "",
                "running_for": p[2] if len(p) > 2 else "",
            })
    ms = round((time.monotonic() - t0) * 1000)
    log_call("list_containers", {"host": host}, containers, ms, host=host)
    return containers


@mcp.tool()
def tail_logs(host: str, container: str, lines: int = 100) -> dict:
    """Digest of recent Docker container logs — level counts, errors, sample lines.

    Returns a compact summary, not raw log lines. Token-efficient by design.

    Args:
        host: Host name from hosts.yaml
        container: Docker container name
        lines: Number of log lines to analyse (max 200)
    """
    import re
    t0 = time.monotonic()
    lines = min(max(1, lines), 200)

    rc, _ = _run_on(host, ["docker", "inspect", "--format", "{{.Name}}", container])
    if rc != 0:
        result = {"ok": False, "error": f"Container '{container}' not found on {host}"}
        log_call("tail_logs", {"host": host, "container": container}, result, 0, allowed=False, host=host)
        return result

    rc, out = _run_on(host, ["docker", "logs", "--tail", str(lines), container], timeout=15)

    ansi = re.compile(r'\x1b\[[0-9;]*m')
    raw_lines = [ansi.sub('', l) for l in out.splitlines() if l.strip()]

    levels: dict[str, list] = {"ERROR": [], "WARN": [], "INFO": [], "OTHER": []}
    timestamps = []
    ts_pat = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}')

    for line in raw_lines:
        m = ts_pat.search(line)
        if m:
            timestamps.append(m.group())
        upper = line.upper()
        if "ERROR" in upper or "EXCEPTION" in upper or "TRACEBACK" in upper:
            levels["ERROR"].append(line)
        elif "WARN" in upper:
            levels["WARN"].append(line)
        elif "INFO" in upper:
            levels["INFO"].append(line)
        else:
            levels["OTHER"].append(line)

    def _sig(line: str) -> str:
        line = ts_pat.sub('', line)
        line = re.sub(r'\d{1,3}(\.\d{1,3}){3}(:\d+)?', '<ip>', line)
        return re.sub(r'\s+', ' ', line).strip()

    seen: set = set()
    unique_info = []
    for line in reversed(levels["INFO"]):
        sig = _sig(line)
        if sig not in seen:
            seen.add(sig)
            unique_info.append(line)
        if len(unique_info) >= 3:
            break

    result = {
        "host": host,
        "container": container,
        "lines_analysed": len(raw_lines),
        "time_range": (
            f"{timestamps[0]} → {timestamps[-1]}" if len(timestamps) >= 2
            else (timestamps[0] if timestamps else "no timestamps")
        ),
        "levels": {k: len(v) for k, v in levels.items()},
        "errors": levels["ERROR"][:10],
        "warnings": levels["WARN"][:10],
        "sample_info": list(reversed(unique_info)),
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("tail_logs", {"host": host, "container": container, "lines": lines}, result, ms, host=host)
    logging.info("tail_logs %s:%s (%d lines, %dms)", host, container, len(raw_lines), ms)
    return result


@mcp.tool()
def safe_restart(host: str, container: str) -> dict:
    """Restart a Docker container. Only containers in the per-host allowlist are accepted.

    Args:
        host: Host name from hosts.yaml
        container: Docker container name to restart
    """
    t0 = time.monotonic()
    allowlist = _allowlist(host)
    if container not in allowlist:
        result = {
            "ok": False,
            "error": f"'{container}' is not in the restart allowlist for '{host}'.",
            "allowlist": sorted(allowlist),
        }
        log_call("safe_restart", {"host": host, "container": container}, result, 0, allowed=False, host=host)
        logging.warning("safe_restart BLOCKED %s:%s", host, container)
        return result

    rc, out = _run_on(host, ["docker", "restart", container], timeout=30)
    result = {"ok": rc == 0, "output": out}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("safe_restart", {"host": host, "container": container}, result, ms, host=host)
    logging.info("safe_restart %s:%s rc=%d (%dms)", host, container, rc, ms)
    return result


@mcp.tool()
def describe_server(host: str) -> str:
    """Topology summary: running containers with ports, plus restart allowlist.

    Args:
        host: Host name from hosts.yaml
    """
    t0 = time.monotonic()
    rc, out = _run_on(host, ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}\t{{.Status}}"])
    cfg = FLEET.get(host, {})
    ssh_addr = cfg.get("ssh", "localhost")
    lines = [f"Server: {host} ({ssh_addr})", "", "Running containers:"]
    if rc == 0:
        for line in out.splitlines():
            lines.append("  " + line)
    lines += ["", f"Restart allowlist: {sorted(_allowlist(host))}"]
    result = "\n".join(lines)
    ms = round((time.monotonic() - t0) * 1000)
    log_call("describe_server", {"host": host}, result, ms, host=host)
    return result


# ── Control-server tools (no host param) ─────────────────────────────────────

@mcp.tool()
def read_doc(name: str) -> str:
    """Read an ops context document stored on the control server.

    Available: ops-map, rules, guard-rules

    Args:
        name: Document name
    """
    if name == "runbook-index":
        books = get_runbooks()
        agent_count = 0
        if _AGENT_RUNBOOK.exists():
            try:
                agent_count = len(json.loads(_AGENT_RUNBOOK.read_text()))
            except Exception:
                pass
        summary = {
            "ops_mcp_runbooks": len(books),
            "ai_agent_runbooks": agent_count,
            "entries": [
                {"id": b["id"], "tool": b["tool"], "target": b["target"],
                 "success_count": b["success_count"], "failure_count": b["failure_count"],
                 "needs_review": b["needs_review"]}
                for b in books
            ],
        }
        log_call("read_doc", {"name": "runbook-index"}, summary, 0)
        return json.dumps(summary, indent=2)

    allowed = {
        "ops-map": "ops-map.md",
        "rules": "rules.md",
        "guard-rules": "guard-rules.yaml",
    }
    if name not in allowed:
        return f"Unknown doc '{name}'. Available: {', '.join(allowed)}, runbook-index"
    path = DOCS_DIR / allowed[name]
    if not path.exists():
        return f"Doc '{name}' not found at {path}."
    content = path.read_text()
    log_call("read_doc", {"name": name}, f"{len(content)} chars", 0)
    return content


def _hetzner_get(path: str) -> dict:
    token = os.environ.get("HETZNER_API_TOKEN", "")
    if not token:
        return {"error": "HETZNER_API_TOKEN not set"}
    url = f"https://api.hetzner.cloud/v1{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _cf_get(path: str) -> dict:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return {"error": "CLOUDFLARE_API_TOKEN not set"}
    url = f"https://api.cloudflare.com/client/v4{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def hetzner_firewall(server: str = "onyx") -> dict:
    """Current Hetzner firewall rules for a server. Read-only.

    Args:
        server: 'onyx' (firewall 10699284) or 'main' (firewall 10646031)
    """
    t0 = time.monotonic()
    fw_ids = {"onyx": 10699284, "main": 10646031}
    if server not in fw_ids:
        return {"ok": False, "error": f"Unknown server '{server}'. Use: {list(fw_ids)}"}
    data = _hetzner_get(f"/firewalls/{fw_ids[server]}")
    if "error" in data:
        return {"ok": False, "error": data["error"]}
    fw = data.get("firewall", {})
    rules = [
        {
            "protocol": r.get("protocol"),
            "port": r.get("port", "any"),
            "sources": r.get("source_ips", []),
            "description": r.get("description", ""),
        }
        for r in fw.get("rules", [])
        if r.get("direction") == "in"
    ]
    result = {"ok": True, "server": server, "firewall_id": fw_ids[server],
              "name": fw.get("name", ""), "inbound_rules": rules, "rule_count": len(rules)}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("hetzner_firewall", {"server": server}, result, ms)
    logging.info("hetzner_firewall %s (%dms)", server, ms)
    return result


@mcp.tool()
def cloudflare_dns(zone: str) -> dict:
    """Current DNS records for a Cloudflare zone. Read-only.

    Args:
        zone: Zone name — edumusik.net, edumusik.com, kita-seminar-manufaktur.de,
              schafliebe.com, evabiallas.com, frid.nu
    """
    t0 = time.monotonic()
    zone_ids = {
        "edumusik.net":               "732a4a0da095167c94fce39b1ea25557",
        "edumusik.com":               "7fa16cc45b82d9593f2faa5f7794933c",
        "kita-seminar-manufaktur.de": "f02fdbb066c0e9ce4221e4ed2488c086",
        "schafliebe.com":             "cb0f8fd6620b2b07e6fd6a80e606f415",
        "evabiallas.com":             "9dc2d9bcbff3ac4aabaeceab3f8bd159",
        "frid.nu":                    "ba84c568d870f43c3ce52a1ab282766b",
    }
    if zone not in zone_ids:
        return {"ok": False, "error": f"Unknown zone '{zone}'. Known: {', '.join(zone_ids)}"}
    data = _cf_get(f"/zones/{zone_ids[zone]}/dns_records?per_page=100")
    if "error" in data:
        return {"ok": False, "error": data["error"]}
    if not data.get("success"):
        return {"ok": False, "error": str(data.get("errors", "unknown"))}
    records = [
        {"type": r["type"], "name": r["name"], "content": r["content"][:80],
         "proxied": r.get("proxied", False), "ttl": r.get("ttl")}
        for r in data.get("result", [])
        if r["type"] in ("A", "AAAA", "CNAME", "MX", "TXT", "NS")
    ]
    result = {"ok": True, "zone": zone, "record_count": len(records), "records": records}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("cloudflare_dns", {"zone": zone}, result, ms)
    logging.info("cloudflare_dns %s (%d records, %dms)", zone, len(records), ms)
    return result


# ── Execution tools ───────────────────────────────────────────────────────────
# All mutation tools use the existing fleet SSH user (stephan on main).
# Safety is enforced by tool-level allowlists — forbidden ops are simply absent.

_WP_CONTAINERS = {
    "edumusik-net-wp", "edumusik-com-wp", "frid-wp",
    "schafliebe-wp", "evabiallas-wp", "ksm-wp",
}

_WP_CLI_WRITE_VERBS = {
    "option update", "option patch", "cache flush", "cron event run",
    "transient delete", "rewrite flush", "config set",
}

_WP_CLI_BLOCKED = {
    "shuffle-salts", "plugin install", "plugin delete", "plugin uninstall",
    "user delete", "db drop", "db reset", "config delete",
}

_COMPOSE_STACKS = {
    "edumusik-net", "edumusik-com", "frid", "schafliebe", "evabiallas", "ksm", "kimai",
}

_SYSTEMCTL_UNITS = {
    "wp-panel", "geoblock-api", "security-dashboard", "wp-file-monitor",
}

_READ_FILE_PREFIXES = (
    "/var/log/", "/srv/", "/opt/", "/usr/local/bin/",
    "/home/stephan/.ops-mcp/", "/var/lib/ai-agent/",
)

_READ_FILE_BLOCKED = ("/etc/ssh/", "/root/", "/etc/sudoers")


@mcp.tool()
def wp_cli(host: str, container: str, cmd: str, write: bool = False) -> dict:
    """Run a WP-CLI command inside a WordPress container.

    Read operations (write=False): safe, no state change.
    Write operations (write=True): must match the write verb allowlist.

    Args:
        host: Host name from hosts.yaml
        container: WordPress container name (e.g. edumusik-net-wp)
        cmd: WP-CLI command without the 'wp' prefix (e.g. 'option get siteurl')
        write: Set True for write operations. Blocked verbs: shuffle-salts,
               plugin install/delete, user delete, db drop/reset.
    """
    t0 = time.monotonic()

    if container not in _WP_CONTAINERS:
        result = {"ok": False, "error": f"Unknown WP container '{container}'. Valid: {sorted(_WP_CONTAINERS)}"}
        log_call("wp_cli", {"host": host, "container": container, "cmd": cmd}, result, 0, allowed=False, host=host)
        return result

    cmd_lower = cmd.lower().strip()
    for blocked in _WP_CLI_BLOCKED:
        if blocked in cmd_lower:
            result = {"ok": False, "error": f"Blocked WP-CLI verb '{blocked}'. Requires Stephan approval."}
            log_call("wp_cli", {"host": host, "container": container, "cmd": cmd}, result, 0, allowed=False, host=host)
            return result

    if write:
        allowed_write = any(cmd_lower.startswith(v) for v in _WP_CLI_WRITE_VERBS)
        if not allowed_write:
            result = {
                "ok": False,
                "error": f"Write verb not in allowlist. Allowed: {sorted(_WP_CLI_WRITE_VERBS)}",
            }
            log_call("wp_cli", {"host": host, "container": container, "cmd": cmd}, result, 0, allowed=False, host=host)
            return result

    user_flag = "" if write else "-u www-data "
    full_cmd = ["sudo", "docker", "exec"] + (["-u", "www-data"] if not write else []) + [container, "wp", "--allow-root"] + cmd.split()
    rc, out = _run_on(host, full_cmd, timeout=30)
    result = {"ok": rc == 0, "output": out[:4000]}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("wp_cli", {"host": host, "container": container, "cmd": cmd, "write": write}, result, ms, host=host)
    logging.info("wp_cli %s:%s '%s' write=%s rc=%d (%dms)", host, container, cmd[:60], write, rc, ms)
    return result


@mcp.tool()
def compose_up(host: str, stack: str) -> dict:
    """Restart a Docker Compose stack with 'docker compose up -d'.

    Only allowlisted stacks can be restarted. Shared infrastructure (traefik,
    shared-infra, monitoring) is not exposed — use break-glass SSH for those.

    Args:
        host: Host name from hosts.yaml
        stack: Stack directory name under /srv/ (e.g. edumusik-net, kimai)
    """
    t0 = time.monotonic()

    if stack not in _COMPOSE_STACKS:
        result = {"ok": False, "error": f"Stack '{stack}' not in allowlist. Allowed: {sorted(_COMPOSE_STACKS)}"}
        log_call("compose_up", {"host": host, "stack": stack}, result, 0, allowed=False, host=host)
        return result

    rc_pre, pre_out = _run_on(host, ["sudo", "docker", "compose", "-f", f"/srv/{stack}/docker-compose.yml", "ps", "--format", "{{.Name}}\t{{.Status}}"], timeout=10)
    pre_state = pre_out.strip()

    rc, out = _run_on(host, ["sudo", "docker", "compose", "-f", f"/srv/{stack}/docker-compose.yml", "up", "-d"], timeout=60)

    rc_post, post_out = _run_on(host, ["sudo", "docker", "compose", "-f", f"/srv/{stack}/docker-compose.yml", "ps", "--format", "{{.Name}}\t{{.Status}}"], timeout=10)
    post_state = post_out.strip()

    verified = rc == 0 and "Up" in post_state
    result = {
        "ok": rc == 0,
        "stack": stack,
        "output": out[:2000],
        "pre_state": pre_state,
        "post_state": post_state,
        "verified": verified,
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("compose_up", {"host": host, "stack": stack}, result, ms, host=host)
    logging.info("compose_up %s:%s rc=%d verified=%s (%dms)", host, stack, rc, verified, ms)
    return result


@mcp.tool()
def systemctl_restart(host: str, unit: str) -> dict:
    """Restart an allowlisted systemd unit and verify it came back active.

    Blocked units (docker, nftables, ssh, ssh.socket) are not in this tool at all.

    Args:
        host: Host name from hosts.yaml
        unit: Systemd unit name (e.g. wp-panel, geoblock-api)
    """
    t0 = time.monotonic()

    if unit not in _SYSTEMCTL_UNITS:
        result = {"ok": False, "error": f"Unit '{unit}' not in allowlist. Allowed: {sorted(_SYSTEMCTL_UNITS)}"}
        log_call("systemctl_restart", {"host": host, "unit": unit}, result, 0, allowed=False, host=host)
        return result

    rc, out = _run_on(host, ["sudo", "systemctl", "restart", unit], timeout=20)
    if rc != 0:
        result = {"ok": False, "error": out}
        log_call("systemctl_restart", {"host": host, "unit": unit}, result, 0, allowed=False, host=host)
        return result

    time.sleep(3)
    rc2, status_out = _run_on(host, ["systemctl", "is-active", unit], timeout=5)
    active = status_out.strip() == "active"

    result = {"ok": active, "unit": unit, "status": status_out.strip(), "restart_output": out}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("systemctl_restart", {"host": host, "unit": unit}, result, ms, host=host)
    logging.info("systemctl_restart %s:%s active=%s (%dms)", host, unit, active, ms)
    return result


@mcp.tool()
def read_file(host: str, path: str, tail_lines: int = 200) -> dict:
    """Read a file from a fleet host. Restricted to safe path prefixes.

    Returns last tail_lines lines for large files (max 200). Max 50KB total.

    Args:
        host: Host name from hosts.yaml
        path: Absolute file path (must be under /var/log/, /srv/, /opt/,
              /usr/local/bin/, /home/stephan/.ops-mcp/, or /var/lib/ai-agent/)
        tail_lines: Number of lines to return if file is large (default 200, max 200)
    """
    t0 = time.monotonic()
    tail_lines = min(max(1, tail_lines), 200)

    for blocked in _READ_FILE_BLOCKED:
        if path.startswith(blocked):
            result = {"ok": False, "error": f"Path '{path}' is blocked."}
            log_call("read_file", {"host": host, "path": path}, result, 0, allowed=False, host=host)
            return result

    if not any(path.startswith(p) for p in _READ_FILE_PREFIXES):
        result = {
            "ok": False,
            "error": f"Path must start with one of: {_READ_FILE_PREFIXES}",
        }
        log_call("read_file", {"host": host, "path": path}, result, 0, allowed=False, host=host)
        return result

    rc, out = _run_on(host, ["tail", f"-{tail_lines}", path], timeout=10)
    if rc != 0:
        result = {"ok": False, "error": out}
        log_call("read_file", {"host": host, "path": path}, result, 0, host=host)
        return result

    content = out[:51200]
    result = {"ok": True, "path": path, "content": content, "truncated": len(out) > 51200}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("read_file", {"host": host, "path": path}, {"ok": True, "bytes": len(content)}, ms, host=host)
    logging.info("read_file %s:%s (%d bytes, %dms)", host, path, len(content), ms)
    return result


_AGENT_RUNBOOK = Path("/var/lib/ai-agent/runbook.json")


@mcp.tool()
def lookup_runbook(problem_description: str) -> dict:
    """Search the remediation runbook for known fixes matching a problem description.

    Searches both the ai-remediation-agent runbook (live fixes learned from
    past incidents) and the ops-mcp runbook KB (MCP tool executions).
    Returns entries ranked by success count. Only entries with >=3 successes
    and >=80% success rate are flagged as safe to auto-execute.

    Args:
        problem_description: Free-text description of the problem or symptom
    """
    t0 = time.monotonic()
    keywords = set(problem_description.lower().split())
    results = []

    # Search ai-remediation-agent runbook (JSON array on main server)
    if _AGENT_RUNBOOK.exists():
        try:
            entries = json.loads(_AGENT_RUNBOOK.read_text())
            for e in entries:
                sig = (e.get("problem_signature") or "").lower()
                score = sum(1 for kw in keywords if kw in sig)
                if score > 0:
                    sc = e.get("success_count", 0)
                    fc = e.get("failure_count", 0)
                    total = sc + fc
                    results.append({
                        "source": "ai-agent",
                        "problem_signature": e.get("problem_signature"),
                        "resolution_steps": e.get("commands_used", []),
                        "success_count": sc,
                        "failure_count": fc,
                        "auto_executable": sc >= 3 and (total == 0 or sc / total >= 0.8),
                        "last_used": e.get("last_used"),
                        "match_score": score,
                    })
        except Exception as ex:
            logging.warning("lookup_runbook: agent runbook read error: %s", ex)

    # Search ops-mcp runbook KB
    for rb in get_runbooks():
        sig = (rb.get("target") or "" + rb.get("problem_hint") or "").lower()
        score = sum(1 for kw in keywords if kw in sig)
        if score > 0:
            sc = rb.get("success_count", 0)
            fc = rb.get("failure_count", 0)
            total = sc + fc
            results.append({
                "source": "ops-mcp",
                "id": rb["id"],
                "tool": rb["tool"],
                "target": rb["target"],
                "resolution": json.loads(rb.get("resolution_json") or "{}"),
                "risk_level": rb.get("risk_level"),
                "success_count": sc,
                "failure_count": fc,
                "auto_executable": sc >= 3 and (total == 0 or sc / total >= 0.8),
                "last_used": rb.get("last_used"),
                "match_score": score,
            })

    results.sort(key=lambda x: (-x["match_score"], -x["success_count"]))
    ms = round((time.monotonic() - t0) * 1000)
    response = {"matches": results[:10], "total_found": len(results)}
    log_call("lookup_runbook", {"problem_description": problem_description}, response, ms)
    return response


@mcp.tool()
def ai_cost_summary(tail: int = 100) -> dict:
    """Return recent AI API call costs from the ai-remediation-agent cost log.

    Each record shows timestamp, model, input/output tokens, and cost in USD.
    Returns the last `tail` records plus a cumulative total.

    Args:
        tail: Number of recent records to return (default 100, max 500)
    """
    t0 = time.monotonic()
    cost_log = Path("/var/lib/ai-agent/cost-log.ndjson")
    if not cost_log.exists():
        return {"error": "Cost log not found — no AI calls have been recorded yet. "
                "The log is written by ai-remediation-agent.py after each Claude API call."}
    tail = min(tail, 500)
    try:
        lines = cost_log.read_text().splitlines()
        records = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        recent = records[-tail:]
        total_in = sum(r.get("input_tokens", 0) for r in records)
        total_out = sum(r.get("output_tokens", 0) for r in records)
        total_cost = sum(r.get("cost_usd", 0) for r in records)
        result = {
            "total_calls": len(records),
            "cumulative": {
                "input_tokens": total_in,
                "output_tokens": total_out,
                "cost_usd": round(total_cost, 4),
            },
            "recent": recent,
        }
    except Exception as e:
        result = {"error": str(e)}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("ai_cost_summary", {"tail": tail}, result, ms)
    return result


if __name__ == "__main__":
    init_db()
    logging.info("ops-mcp starting (name=%s, fleet=%s, pid=%d)",
                 _MCP_NAME, list(FLEET), os.getpid())
    mcp.run(transport="stdio")
