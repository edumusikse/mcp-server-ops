#!/usr/bin/env python3
"""Block direct SSH/server bash commands — force MCP tool use instead.

Intent: keep `ssh onyx ...` as the slow/discouraged path so Claude routes
through the ops MCP in the normal case. Two deliberate escape hatches:

1. `ssh onyx-bash ...` (and sftp/rsync via the same alias) is always allowed
   — this is the non-FIDO fallback for when MCP is down. See ~/.ssh/config.

2. `/tmp/claude-hook-bypass` containing literal `CONFIRMED` unblocks
   everything for 300 seconds. Documented in ~/.claude/CLAUDE.md and
   ~/EMERGENCY-CLAUDE-HOOK-BYPASS.md.
"""
import json
import os
import re
import sys
import time

BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300

BLOCK_RE = re.compile(r"^\s*(ssh|sftp|scp|rsync|docker|kubectl)\b")
FALLBACK_ALIAS_RE = re.compile(r"\b(onyx-bash)\b")


def bypass_active() -> bool:
    try:
        st = os.stat(BYPASS_FILE)
    except FileNotFoundError:
        return False
    if time.time() - st.st_mtime > BYPASS_TTL_SEC:
        return False
    try:
        with open(BYPASS_FILE) as f:
            return f.read().strip() == "CONFIRMED"
    except OSError:
        return False


def allow_fallback(cmd: str) -> bool:
    """Allow ssh/sftp/scp/rsync invocations that target the onyx-bash alias."""
    if not re.match(r"^\s*(ssh|sftp|scp|rsync)\b", cmd):
        return False
    return bool(FALLBACK_ALIAS_RE.search(cmd))


def decide(cmd: str) -> dict:
    if bypass_active():
        return {"decision": "allow"}
    if allow_fallback(cmd):
        return {"decision": "allow"}
    if BLOCK_RE.match(cmd):
        return {
            "decision": "block",
            "reason": (
                "Direct SSH/docker/kubectl is disabled in ops-agent. "
                "Use the ops MCP tools (mcp__ops__*). If MCP is down, use "
                "`ssh onyx-bash ...` for the non-FIDO fallback, or write "
                "'CONFIRMED' to /tmp/claude-hook-bypass for a 5-minute unblock."
            ),
        }
    return {"decision": "allow"}


def main() -> None:
    payload = json.load(sys.stdin)
    cmd = payload.get("tool_input", {}).get("command", "")
    print(json.dumps(decide(cmd)))


if __name__ == "__main__":
    main()
