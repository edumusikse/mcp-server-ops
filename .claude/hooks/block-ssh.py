#!/usr/bin/env python3
"""Block direct SSH/server bash commands — force MCP tool use instead.

Intent: keep `ssh onyx ...` as the slow/discouraged path so Claude routes
through the ops MCP in the normal case. Escape hatches are intentionally
symmetrical with budget_guard.py so one mental model covers both hooks.

Escape hatches (checked BEFORE block patterns, in this order):

  1. KILL SWITCH — `~/.ops-mcp/block-ssh-off` exists → exit 0 immediately.
     No TTL, no content match. Presence = off. Reliable escape if the
     block pattern itself misfires.

     Toggle: `touch ~/.ops-mcp/block-ssh-off`   # off
             `rm ~/.ops-mcp/block-ssh-off`      # on

  2. BYPASS FILE — `/tmp/claude-hook-bypass` whose first whitespace-
     delimited token is "CONFIRMED", mtime within 300s. Identical parsing
     to budget_guard so a single bypass write unlocks both hooks.

  3. FALLBACK ALIAS — `ssh onyx-bash ...` (and sftp/scp/rsync on the same
     alias) is always allowed — this is the non-FIDO fallback for when
     MCP is down. See ~/.ssh/config.

Fail-open invariants (mirrors budget_guard):
    - Malformed stdin JSON     → exit 0 (allow)
    - Missing tool_input       → exit 0 (allow)
    - Unhandled exception      → exit 0 (never lock out)

Exit codes:
    0 = allow    2 = block (stderr carries the reason)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "block-ssh-off"
BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
BYPASS_TOKEN = "CONFIRMED"

BLOCK_RE = re.compile(
    r"^\s*(?:(?:sudo|command)\s+(?:-\S+\s+)*(?:\S+\s+)?|"
    r"env\s+(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*)*"
    r"(ssh|sftp|scp|rsync|docker|kubectl)\b"
)
SEGMENT_SPLIT_RE = re.compile(r"(?:&&|\|\||[;\n|])")
FALLBACK_ALIAS_RE = re.compile(r"\b(onyx-bash)\b")


def kill_switch_active() -> bool:
    return KILL_SWITCH.exists()


def bypass_active() -> bool:
    try:
        st = os.stat(BYPASS_FILE)
    except FileNotFoundError:
        return False
    if time.time() - st.st_mtime > BYPASS_TTL_SEC:
        return False
    try:
        with open(BYPASS_FILE) as f:
            content = f.read().strip()
    except OSError:
        return False
    if not content:
        return False
    return content.split()[0] == BYPASS_TOKEN


def command_segments(cmd: str) -> list[str]:
    """Best-effort shell command segmentation for guard matching."""
    return [s.strip() for s in SEGMENT_SPLIT_RE.split(cmd) if s.strip()]


def allow_fallback(cmd: str) -> bool:
    """Allow ssh/sftp/scp/rsync invocations that target the onyx-bash alias."""
    if not re.match(
        r"^\s*(?:(?:sudo|command)\s+(?:-\S+\s+)*(?:\S+\s+)?|"
        r"env\s+(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*)*"
        r"(ssh|sftp|scp|rsync)\b",
        cmd,
    ):
        return False
    return bool(FALLBACK_ALIAS_RE.search(cmd))


def blocked_segment(cmd: str) -> str | None:
    """Return the first blocked shell segment, ignoring the onyx-bash fallback."""
    for segment in command_segments(cmd):
        if allow_fallback(segment):
            continue
        if BLOCK_RE.match(segment):
            return segment
    return None


def decide(cmd: str, kill: bool, bypass: bool) -> dict:
    """Pure decision. Precedence: kill > bypass > fallback > block."""
    if kill:
        return {"decision": "allow", "level": "kill"}
    if bypass:
        return {"decision": "allow", "level": "bypass"}
    blocked = blocked_segment(cmd)
    if blocked:
        tool = BLOCK_RE.match(blocked).group(1) if BLOCK_RE.match(blocked) else "command"
        return {
            "decision": "block",
            "level": "hard",
            "reason": (
                f"Direct SSH/docker/kubectl is disabled in ops-agent "
                f"(blocked segment: {blocked!r}). "
                "Use the ops MCP tools (mcp__ops__*). If MCP is down, use "
                "`ssh onyx-bash ...` for the non-FIDO fallback. "
                "To lift this hook: `touch ~/.ops-mcp/block-ssh-off`  (or "
                "write 'CONFIRMED' to /tmp/claude-hook-bypass for 5 min)."
            ),
            "tool": tool,
        }
    if command_segments(cmd) and all(allow_fallback(s) for s in command_segments(cmd)):
        return {"decision": "allow", "level": "fallback"}
    return {"decision": "allow", "level": "ok"}


def emit_pre_tool_use_context(message: str) -> None:
    """Emit PreToolUse extra context via the spec-correct envelope."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": message,
        }
    }))


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            return 0  # malformed payload: never block
        cmd = payload.get("tool_input", {}).get("command", "")

        result = decide(
            cmd,
            kill=kill_switch_active(),
            bypass=bypass_active(),
        )

        if result["decision"] == "block":
            print(result["reason"], file=sys.stderr)
            return 2

        level = result.get("level")
        if level == "bypass":
            emit_pre_tool_use_context(
                f"SSH-BLOCK BYPASS active ({BYPASS_FILE}). TTL {BYPASS_TTL_SEC}s."
            )
        elif level == "kill":
            emit_pre_tool_use_context(
                f"SSH-BLOCK KILL SWITCH on ({KILL_SWITCH}). Hook fully disabled."
            )
        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
