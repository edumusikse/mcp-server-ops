#!/usr/bin/env python3
"""
ops-mcp: Server-side MCP daemon for onyx.

Guards live at execution point. Every tool call is logged to shared SQLite.
NEVER print to stdout — that is the JSON-RPC transport channel.

Transport: stdio
Connect via: ssh onyx /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/server.py
"""

import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# All logging goes to file, never stdout (stdout = MCP transport)
_LOG_DIR = Path(os.environ.get("OPS_STATE_DIR", str(Path.home() / ".ops-mcp")))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(_LOG_DIR / "ops-mcp.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

sys.path.insert(0, "/opt/ops-mcp")
from state import init_db, log_call, save_snapshot  # noqa: E402

from mcp.server.fastmcp import FastMCP  # noqa: E402

_SERVER_NAME = os.environ.get("OPS_SERVER_NAME", "onyx")
mcp = FastMCP(f"{_SERVER_NAME}-ops")

# Containers that may be restarted — expand per-server via OPS_RESTART_ALLOWLIST env var
# Format: comma-separated container names, e.g. "beszel-agent,nginx"
_allowlist_env = os.environ.get("OPS_RESTART_ALLOWLIST", "beszel-agent")
RESTART_ALLOWLIST: set[str] = {s.strip() for s in _allowlist_env.split(",") if s.strip()}

DOCS_DIR = Path("/opt/ops-mcp/docs")


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Run subprocess, return (returncode, combined stdout+stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as e:
        return 1, str(e)


@mcp.tool()
def server_status() -> dict:
    """Pre-digested server state: containers running/stopped, disk %, RAM %, uptime.

    Returns a compact summary — not raw command output. Token-efficient by design.
    """
    t0 = time.monotonic()

    rc, out = _run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"])
    containers = []
    if rc == 0:
        for line in out.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers.append({"name": parts[0], "status": parts[1]})

    rc, out = _run(["df", "-h", "/", "--output=pcent"])
    disk_pct = out.splitlines()[-1].strip().rstrip("%") if rc == 0 else "?"

    rc, out = _run(["free", "-m"])
    ram: dict = {}
    for line in out.splitlines():
        if line.startswith("Mem:"):
            p = line.split()
            if len(p) >= 3:
                total, used = int(p[1]), int(p[2])
                ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

    rc, out = _run(["uptime", "-p"])
    uptime = out if rc == 0 else "?"

    result = {
        "containers": containers,
        "container_count": len(containers),
        "disk_pct": disk_pct,
        "ram": ram,
        "uptime": uptime,
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("server_status", {}, result, ms)
    save_snapshot(result)
    logging.info("server_status called (%dms)", ms)
    return result


@mcp.tool()
def list_containers() -> list:
    """All Docker containers (running and stopped) with name, status, and age."""
    t0 = time.monotonic()
    rc, out = _run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.RunningFor}}"])
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
    log_call("list_containers", {}, containers, ms)
    return containers


@mcp.tool()
def tail_logs(container: str, lines: int = 100) -> dict:
    """Digest of recent Docker container logs. Processes locally — returns a compact summary, not raw lines.

    Returns: line count, level breakdown, time range, any ERROR/WARN lines (up to 10), and
    a sample of non-repetitive INFO lines. Token-efficient by design.

    Args:
        container: Docker container name
        lines: Number of log lines to analyse (max 200)
    """
    import re
    t0 = time.monotonic()
    lines = min(max(1, lines), 200)

    rc, _ = _run(["docker", "inspect", "--format", "{{.Name}}", container])
    if rc != 0:
        result = {"ok": False, "error": f"Container '{container}' not found"}
        log_call("tail_logs", {"container": container, "lines": lines}, result, 0, allowed=False)
        return result

    rc, out = _run(["docker", "logs", "--tail", str(lines), container], timeout=15)

    # Strip ANSI escape codes
    ansi = re.compile(r'\x1b\[[0-9;]*m')
    raw_lines = [ansi.sub('', l) for l in out.splitlines() if l.strip()]

    levels = {"ERROR": [], "WARN": [], "INFO": [], "OTHER": []}
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

    # Deduplicate INFO lines — keep unique message patterns (strip timestamps/IPs)
    def _sig(line: str) -> str:
        line = ts_pat.sub('', line)
        line = re.sub(r'\d{1,3}(\.\d{1,3}){3}(:\d+)?', '<ip>', line)
        return re.sub(r'\s+', ' ', line).strip()

    seen_sigs: set = set()
    unique_info = []
    for line in reversed(levels["INFO"]):
        sig = _sig(line)
        if sig not in seen_sigs:
            seen_sigs.add(sig)
            unique_info.append(line)
        if len(unique_info) >= 3:
            break

    result = {
        "container": container,
        "lines_analysed": len(raw_lines),
        "time_range": f"{timestamps[0]} → {timestamps[-1]}" if len(timestamps) >= 2 else (timestamps[0] if timestamps else "no timestamps"),
        "levels": {k: len(v) for k, v in levels.items()},
        "errors": levels["ERROR"][:10],
        "warnings": levels["WARN"][:10],
        "sample_info": list(reversed(unique_info)),
    }

    ms = round((time.monotonic() - t0) * 1000)
    log_call("tail_logs", {"container": container, "lines": lines}, result, ms)
    logging.info("tail_logs %s (%d lines, %dms)", container, len(raw_lines), ms)
    return result


@mcp.tool()
def safe_restart(container: str) -> dict:
    """Restart a Docker container. Only allowlisted containers are accepted.

    Args:
        container: Docker container name to restart
    """
    t0 = time.monotonic()
    if container not in RESTART_ALLOWLIST:
        result = {
            "ok": False,
            "error": f"'{container}' is not in the restart allowlist.",
            "allowlist": sorted(RESTART_ALLOWLIST),
        }
        log_call("safe_restart", {"container": container}, result, 0, allowed=False)
        logging.warning("safe_restart BLOCKED: %s", container)
        return result

    rc, out = _run(["docker", "restart", container], timeout=30)
    result = {"ok": rc == 0, "output": out}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("safe_restart", {"container": container}, result, ms)
    logging.info("safe_restart %s rc=%d (%dms)", container, rc, ms)
    return result


@mcp.tool()
def describe_server() -> str:
    """Topology summary: what services exist on this server and their purpose."""
    t0 = time.monotonic()
    rc, out = _run(["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}\t{{.Status}}"])
    _server_ip = os.environ.get("OPS_SERVER_IP", "")
    _label = f"{_SERVER_NAME} ({_server_ip})" if _server_ip else _SERVER_NAME
    lines = [f"Server: {_label}", "", "Running containers:"]
    if rc == 0:
        for line in out.splitlines():
            lines.append("  " + line)
    lines += ["", f"Restart allowlist: {sorted(RESTART_ALLOWLIST)}"]
    result = "\n".join(lines)
    ms = round((time.monotonic() - t0) * 1000)
    log_call("describe_server", {}, result, ms)
    return result


@mcp.tool()
def read_doc(name: str) -> str:
    """Read an ops context document stored on this server.

    Available documents:
    - ops-map: Container names, ports, compose paths for all servers
    - rules: Behavioural rules and operational guardrails
    - guard-rules: Guard rule patterns (YAML)

    Args:
        name: Document name (ops-map, rules, or guard-rules)
    """
    allowed = {
        "ops-map": "ops-map.md",
        "rules": "rules.md",
        "guard-rules": "guard-rules.yaml",
    }
    if name not in allowed:
        return f"Unknown doc '{name}'. Available: {', '.join(allowed)}"
    path = DOCS_DIR / allowed[name]
    if not path.exists():
        return f"Doc '{name}' not yet synced to {path}. Run: rsync from Mac."
    content = path.read_text()
    log_call("read_doc", {"name": name}, f"{len(content)} chars", 0)
    return content


def _hetzner_get(path: str) -> dict:
    """Call Hetzner Cloud API. Token from HETZNER_API_TOKEN env var."""
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
    """Call Cloudflare API. Token from CLOUDFLARE_API_TOKEN env var."""
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

    Returns allowed inbound rules as a compact list — not raw API JSON.

    Args:
        server: 'onyx' (firewall 10699284) or 'main' (firewall 10646031)
    """
    t0 = time.monotonic()
    fw_ids = {"onyx": 10699284, "main": 10646031}
    if server not in fw_ids:
        return {"ok": False, "error": f"Unknown server '{server}'. Use 'onyx' or 'main'."}

    fw_id = fw_ids[server]
    data = _hetzner_get(f"/firewalls/{fw_id}")

    if "error" in data:
        return {"ok": False, "error": data["error"]}

    fw = data.get("firewall", {})
    rules = []
    for r in fw.get("rules", []):
        if r.get("direction") == "in":
            rules.append({
                "protocol": r.get("protocol"),
                "port": r.get("port", "any"),
                "sources": r.get("source_ips", []),
                "description": r.get("description", ""),
            })

    result = {
        "ok": True,
        "server": server,
        "firewall_id": fw_id,
        "name": fw.get("name", ""),
        "inbound_rules": rules,
        "rule_count": len(rules),
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("hetzner_firewall", {"server": server}, result, ms)
    logging.info("hetzner_firewall %s (%dms)", server, ms)
    return result


@mcp.tool()
def cloudflare_dns(zone: str) -> dict:
    """Current DNS records for a Cloudflare zone. Read-only.

    Returns A, CNAME, MX, TXT records as a compact list.

    Args:
        zone: Zone name — one of: edumusik.net, edumusik.com,
              kita-seminar-manufaktur.de, schafliebe.com, evabiallas.com, frid.nu
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

    zone_id = zone_ids[zone]
    data = _cf_get(f"/zones/{zone_id}/dns_records?per_page=100")

    if "error" in data:
        return {"ok": False, "error": data["error"]}
    if not data.get("success"):
        return {"ok": False, "error": str(data.get("errors", "unknown error"))}

    records = []
    for r in data.get("result", []):
        if r["type"] in ("A", "AAAA", "CNAME", "MX", "TXT", "NS"):
            records.append({
                "type": r["type"],
                "name": r["name"],
                "content": r["content"][:80],
                "proxied": r.get("proxied", False),
                "ttl": r.get("ttl"),
            })

    result = {
        "ok": True,
        "zone": zone,
        "record_count": len(records),
        "records": records,
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("cloudflare_dns", {"zone": zone}, result, ms)
    logging.info("cloudflare_dns %s (%d records, %dms)", zone, len(records), ms)
    return result


if __name__ == "__main__":
    init_db()
    logging.info("ops-mcp server starting (pid=%d)", __import__("os").getpid())
    mcp.run(transport="stdio")
