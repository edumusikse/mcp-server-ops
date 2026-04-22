"""File I/O tools — read_file (inspection) and write_file (config deploy).

Payload-similarity guard wires in here too, to catch Bash→Read→write_file shuttles.
"""
from __future__ import annotations

import base64
import logging
import shlex
import time

from guards import thrash_guard as _thrash_guard, payload_similarity_guard as _payload_guard
from state import log_call
from transport import mcp, run_on

_READ_FILE_PREFIXES = (
    "/var/log/", "/srv/", "/opt/", "/usr/local/bin/",
    "/home/stephan/.ops-mcp/", "/var/lib/ai-agent/",
)

_READ_FILE_BLOCKED = ("/etc/ssh/", "/root/", "/etc/sudoers")

# write_file has a tighter allowlist than read_file — config surfaces only,
# never /var/log or /srv. /srv/ stays deploy.py territory.
_WRITE_FILE_PREFIXES = (
    "/opt/ops-mcp/",           # MCP self-mutation (probes, hosts.yaml, server.py)
    "/opt/validator/",         # validator checks yaml
    "/opt/inspec/",            # inspec profiles + runner
    "/opt/security-audit/",    # security audit dashboard + backend
    "/opt/wp-panel/",          # wp-panel Flask app
    "/usr/local/bin/checks/",  # alt validator checks location
    "/usr/local/bin/probes/",  # alt probes location
    "/usr/local/bin/",         # ops scripts (inspec wrapper, etc.)
    "/etc/cron.d/",            # cron jobs (wrapper scripts, timeouts)
)
_WRITE_FILE_BLOCKED = (
    "/etc/ssh/", "/root/", "/etc/sudoers", "/etc/passwd", "/etc/shadow",
    "/etc/nftables.conf", "/etc/systemd/system/ssh",
)
_WRITE_FILE_MAX_BYTES = 256 * 1024


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

    stop = _thrash_guard("read_file", path)
    if stop:
        log_call("read_file", {"host": host, "path": path}, stop, 0, allowed=False, host=host, needs_review=True)
        return stop

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

    rc, out = run_on(host, ["tail", f"-{tail_lines}", path], timeout=10)
    if rc != 0:
        result = {"ok": False, "error": out}
        log_call("read_file", {"host": host, "path": path}, result, 0, host=host)
        return result

    content = out[:51200]
    stop = _payload_guard("read_file", content)
    if stop:
        log_call("read_file", {"host": host, "path": path}, stop, 0, allowed=False, host=host, needs_review=True)
        return stop
    result = {"ok": True, "path": path, "content": content, "truncated": len(out) > 51200}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("read_file", {"host": host, "path": path}, {"ok": True, "bytes": len(content)}, ms, host=host)
    logging.info("read_file %s:%s (%d bytes, %dms)", host, path, len(content), ms)
    return result


@mcp.tool()
def write_file(host: str, path: str, content: str, sudo: bool = False) -> dict:
    """Write a file on a fleet host. Tighter allowlist than read_file.

    Atomically writes via temp file + mv. Always backs up the existing file
    to <path>.bak.<ts> before replacing it. All writes logged to state.db
    and surface in the review queue.

    Allowed prefixes: /opt/ops-mcp/, /opt/validator/, /opt/inspec/,
    /opt/security-audit/, /opt/wp-panel/, /usr/local/bin/, /etc/cron.d/.
    Blocked: /etc/ssh/, /root/, /etc/sudoers, /etc/passwd, /etc/shadow,
    /etc/nftables.conf, /etc/systemd/system/ssh*.

    Args:
        host: Host name from hosts.yaml
        path: Absolute file path within the write allowlist
        content: New file content (max 256 KB)
        sudo: Use sudo -n for write (required for /usr/local/bin, /etc/cron.d)
    """
    t0 = time.monotonic()
    args = {"host": host, "path": path, "bytes": len(content), "sudo": sudo}

    for blocked in _WRITE_FILE_BLOCKED:
        if path.startswith(blocked):
            result = {"ok": False, "error": f"Path '{path}' is blocked for writes."}
            log_call("write_file", args, result, 0, allowed=False, host=host)
            return result

    if not any(path.startswith(p) for p in _WRITE_FILE_PREFIXES):
        result = {
            "ok": False,
            "error": f"Write path must start with one of: {_WRITE_FILE_PREFIXES}",
        }
        log_call("write_file", args, result, 0, allowed=False, host=host)
        return result

    if len(content.encode("utf-8")) > _WRITE_FILE_MAX_BYTES:
        result = {"ok": False, "error": f"Content > {_WRITE_FILE_MAX_BYTES} bytes"}
        log_call("write_file", args, result, 0, allowed=False, host=host)
        return result

    stop = _payload_guard("write_file", content)
    if stop:
        log_call("write_file", args, stop, 0, allowed=False, host=host, needs_review=True)
        return stop

    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    sudo_prefix = "sudo -n " if sudo else ""

    # Heredoc avoids ARG_MAX and quoting issues for large base64 payloads.
    shell_cmd = (
        f"set -e; "
        f"tmp=$(mktemp); "
        f"base64 -d > \"$tmp\" <<'B64EOF'\n{encoded}\nB64EOF\n"
        f"if [ -e {shlex.quote(path)} ]; then "
        f"  {sudo_prefix}cp -p {shlex.quote(path)} {shlex.quote(path)}.bak.{ts}; "
        f"fi; "
        f"{sudo_prefix}install -m 0644 \"$tmp\" {shlex.quote(path)}; "
        f"rm -f \"$tmp\"; "
        f"echo OK"
    )

    rc, out = run_on(host, ["sh", "-c", shell_cmd], timeout=30)
    if rc != 0 or not out.strip().endswith("OK"):
        result = {"ok": False, "error": out or f"rc={rc}"}
        log_call("write_file", args, result, 0, host=host)
        return result

    result = {
        "ok": True, "path": path, "bytes": len(content),
        "backup": f"{path}.bak.{ts}",
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("write_file", args, result, ms, host=host)
    logging.info("write_file %s:%s (%d bytes, %dms)", host, path, len(content), ms)
    return result
