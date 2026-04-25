#!/usr/bin/env python3
"""Block write_file calls to /opt paths that omit sudo=True.

Without sudo=True the MCP user can't back up the target file — the atomic
write fails with Permission Denied, leaving a partial temp file.

Affected: /opt/security-audit/, /opt/wp-panel/, /usr/local/bin/, /etc/cron.d/
Exempt:   /opt/ops-mcp/ — MCP user owns it, no sudo needed.

Escape hatches (checked in order):
  1. ~/.ops-mcp/sudo-guard-off  (kill switch, no TTL)
  2. /tmp/claude-hook-bypass containing CONFIRMED  (300s TTL)

Fail-open: any exception → exit 0.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "sudo-guard-off"
BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
BYPASS_TOKEN = "CONFIRMED"

SUDO_REQUIRED_PREFIXES = [
    "/opt/security-audit/",
    "/opt/wp-panel/",
    "/usr/local/bin/",
    "/etc/cron.d/",
]

BLOCK_MESSAGE = (
    "WRITE-FILE-SUDO: path requires sudo=True.\n"
    "Without it the backup step fails with Permission Denied.\n"
    "Add sudo=True to the write_file call.\n\n"
    "Paths requiring sudo: /opt/security-audit/, /opt/wp-panel/, "
    "/usr/local/bin/, /etc/cron.d/\n"
    "Exception: /opt/ops-mcp/ (MCP user owns it, no sudo needed)."
)


def bypass_active() -> bool:
    if KILL_SWITCH.exists():
        return True
    try:
        p = Path(BYPASS_FILE)
        if p.exists() and (time.time() - p.stat().st_mtime) < BYPASS_TTL_SEC:
            return p.read_text().split()[0] == BYPASS_TOKEN
    except Exception:
        pass
    return False


def main() -> int:
    try:
        if bypass_active():
            return 0

        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            return 0

        if payload.get("tool_name") != "mcp__ops__write_file":
            return 0

        tool_input = payload.get("tool_input") or {}
        path = tool_input.get("path") or ""
        sudo = tool_input.get("sudo", False)

        if sudo:
            return 0

        for prefix in SUDO_REQUIRED_PREFIXES:
            if path.startswith(prefix):
                print(BLOCK_MESSAGE, file=sys.stderr)
                return 2

        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
