"""Fleet inspection tools — server_status, fleet_status, list_containers, tail_logs,
safe_restart, describe_server, systemctl_restart."""
from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor

from guards import thrash_guard as _thrash_guard
from state import log_call, save_snapshot
from transport import FLEET, allowlist, mcp, run_on

_SYSTEMCTL_UNITS = {
    "wp-panel", "geoblock-api", "security-dashboard", "wp-file-monitor",
}


@mcp.tool()
def server_status(host: str) -> dict:
    """Pre-digested server state: containers, disk %, RAM %, uptime.

    Args:
        host: Host name from hosts.yaml (e.g. 'onyx', 'main')
    """
    t0 = time.monotonic()

    rc, out = run_on(host, ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"])
    containers = []
    if rc == 0:
        for line in out.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers.append({"name": parts[0], "status": parts[1]})

    rc, out = run_on(host, ["df", "-h", "/", "--output=pcent"])
    disk_pct = "?"
    if rc == 0:
        for line in out.splitlines():
            val = line.strip().rstrip("%")
            if val.isdigit():
                disk_pct = val
                break

    rc, out = run_on(host, ["free", "-m"])
    ram: dict = {}
    for line in out.splitlines():
        if line.startswith("Mem:"):
            p = line.split()
            if len(p) >= 3:
                total, used = int(p[1]), int(p[2])
                ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

    rc, out = run_on(host, ["uptime", "-p"])
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
            rc, out = run_on(hostname, ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"])
            containers = []
            if rc == 0:
                for line in out.splitlines():
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        containers.append({"name": parts[0], "status": parts[1]})

            rc, out = run_on(hostname, ["df", "-h", "/", "--output=pcent"])
            disk_pct = out.splitlines()[-1].strip().rstrip("%") if rc == 0 else "?"

            rc, out = run_on(hostname, ["free", "-m"])
            ram: dict = {}
            for line in out.splitlines():
                if line.startswith("Mem:"):
                    p = line.split()
                    if len(p) >= 3:
                        total, used = int(p[1]), int(p[2])
                        ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

            rc, out = run_on(hostname, ["uptime", "-p"])
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
    rc, out = run_on(host, ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.RunningFor}}"])
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
    t0 = time.monotonic()
    lines = min(max(1, lines), 200)

    stop = _thrash_guard("tail_logs", container)
    if stop:
        log_call("tail_logs", {"host": host, "container": container}, stop, 0, allowed=False, host=host, needs_review=True)
        return stop

    rc, _ = run_on(host, ["docker", "inspect", "--format", "{{.Name}}", container])
    if rc != 0:
        result = {"ok": False, "error": f"Container '{container}' not found on {host}"}
        log_call("tail_logs", {"host": host, "container": container}, result, 0, allowed=False, host=host)
        return result

    rc, out = run_on(host, ["docker", "logs", "--tail", str(lines), container], timeout=15)

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
    al = allowlist(host)
    if container not in al:
        result = {
            "ok": False,
            "error": f"'{container}' is not in the restart allowlist for '{host}'.",
            "allowlist": sorted(al),
        }
        log_call("safe_restart", {"host": host, "container": container}, result, 0, allowed=False, host=host)
        logging.warning("safe_restart BLOCKED %s:%s", host, container)
        return result

    rc, out = run_on(host, ["docker", "restart", container], timeout=30)
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
    rc, out = run_on(host, ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}\t{{.Status}}"])
    cfg = FLEET.get(host, {})
    ssh_addr = cfg.get("ssh", "localhost")
    lines = [f"Server: {host} ({ssh_addr})", "", "Running containers:"]
    if rc == 0:
        for line in out.splitlines():
            lines.append("  " + line)
    lines += ["", f"Restart allowlist: {sorted(allowlist(host))}"]
    result = "\n".join(lines)
    ms = round((time.monotonic() - t0) * 1000)
    log_call("describe_server", {"host": host}, result, ms, host=host)
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

    rc, out = run_on(host, ["sudo", "systemctl", "restart", unit], timeout=20)
    if rc != 0:
        result = {"ok": False, "error": out}
        log_call("systemctl_restart", {"host": host, "unit": unit}, result, 0, allowed=False, host=host)
        return result

    time.sleep(3)
    rc2, status_out = run_on(host, ["systemctl", "is-active", unit], timeout=5)
    active = status_out.strip() == "active"

    result = {"ok": active, "unit": unit, "status": status_out.strip(), "restart_output": out}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("systemctl_restart", {"host": host, "unit": unit}, result, ms, host=host)
    logging.info("systemctl_restart %s:%s active=%s (%dms)", host, unit, active, ms)
    return result


@mcp.tool()
def apt_upgrade(host: str, dry_run: bool = True) -> dict:
    """Apply OS package security upgrades via apt-get.

    dry_run=True (default) shows what would be upgraded without applying.
    dry_run=False runs the upgrade. Safe to run; does not dist-upgrade or
    remove packages.

    Args:
        host: Host name from hosts.yaml
        dry_run: Simulate only when True (default True for safety)
    """
    t0 = time.monotonic()

    rc_upd, upd_out = run_on(host, ["sudo", "apt-get", "update", "-qq"], timeout=60)
    if rc_upd != 0:
        result = {"ok": False, "stage": "apt-get update", "error": upd_out}
        log_call("apt_upgrade", {"host": host, "dry_run": dry_run}, result, 0, host=host)
        return result

    if dry_run:
        rc, out = run_on(host, ["apt-get", "--simulate", "upgrade"], timeout=60)
        upgradable = [l for l in out.splitlines() if l.startswith("Inst ")]
        result = {
            "ok": True,
            "dry_run": True,
            "packages_to_upgrade": len(upgradable),
            "packages": upgradable[:50],
        }
    else:
        rc, out = run_on(
            host,
            ["sudo", "env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "upgrade", "-y"],
            timeout=300,
        )
        tail = out[-3000:] if len(out) > 3000 else out
        result = {"ok": rc == 0, "dry_run": False, "output": tail}

    ms = round((time.monotonic() - t0) * 1000)
    log_call("apt_upgrade", {"host": host, "dry_run": dry_run}, result, ms, host=host)
    logging.info("apt_upgrade %s dry_run=%s ok=%s (%dms)", host, dry_run, result["ok"], ms)
    return result
