"""WP-CLI tool — verb allowlists + thrash-guarded exec inside WordPress containers."""
from __future__ import annotations

import logging
import shlex
import time

from guards import thrash_guard as _thrash_guard
from state import log_call
from transport import mcp, run_on

_WP_CONTAINERS = {
    "edumusik-net-wp", "edumusik-com-wp", "frid-wp",
    "schafliebe-wp", "evabiallas-wp", "ksm-wp",
}

_WP_CLI_WRITE_VERBS = {
    "option update", "option patch", "option delete", "option add",
    "cache flush", "transient delete", "rewrite flush", "config set",
    "cron event run", "cron event delete", "cron event schedule",
    "plugin activate", "plugin deactivate", "plugin update", "plugin toggle",
    "theme activate", "theme update",
    "user update", "user create", "user set-role", "user add-role", "user remove-role",
    "post update", "post create", "post meta update", "post meta add", "post meta delete",
    "post term set", "post term add", "post term remove",
    "term update", "term create",
    "search-replace",
    "language core install", "language core update", "language plugin install",
    "eval", "eval-file",
    "media regenerate",
    "role create", "cap add",
}

_WP_CLI_BLOCKED = {
    "shuffle-salts", "plugin install", "plugin delete", "plugin uninstall",
    "user delete", "db drop", "db reset", "config delete",
}


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

    stop = _thrash_guard("wp_cli", container)
    if stop:
        log_call("wp_cli", {"host": host, "container": container, "cmd": cmd}, stop, 0, allowed=False, host=host, needs_review=True)
        return stop

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

    try:
        cmd_parts = shlex.split(cmd)
    except ValueError as e:
        result = {"ok": False, "error": f"Invalid shell quoting in cmd: {e}"}
        log_call("wp_cli", {"host": host, "container": container, "cmd": cmd}, result, 0, allowed=False, host=host)
        return result

    full_cmd = ["sudo", "docker", "exec"] + (["-u", "www-data"] if not write else []) + [container, "wp", "--allow-root"] + cmd_parts
    rc, out = run_on(host, full_cmd, timeout=30)
    result = {"ok": rc == 0, "output": out[:4000]}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("wp_cli", {"host": host, "container": container, "cmd": cmd, "write": write}, result, ms, host=host)
    logging.info("wp_cli %s:%s '%s' write=%s rc=%d (%dms)", host, container, cmd[:60], write, rc, ms)
    return result
