#!/usr/bin/env python3
"""Plan-first guard: require TodoWrite before a 4th consecutive Bash call.

Prevents exploration-by-command — chains of Bash calls discovering state
that a single Read would have answered. Forces a planning step (TodoWrite)
before executing sequences of shell commands.

Wired as PreToolUse with matcher "Bash".

Logic:
  1. Scan the session transcript for tool_use events.
  2. Count consecutive Bash calls at the tail (resets on any non-Bash tool).
  3. Check whether TodoWrite has been called anywhere in the session.
  4. If consecutive Bash >= BASH_STREAK_LIMIT and no TodoWrite → deny.

Threshold is 3 (block on 4th consecutive), not 2, so that short intentional
sequences (git add → commit → push) are not interrupted — those are execution,
not exploration. The problem pattern is 4+ Bash calls: find + ls + git status
+ chmod + ...

Escape hatches (same pattern as budget_guard / runbook_guard):
  1. KILL SWITCH  — ~/.ops-mcp/plan-guard-off exists → allow (no TTL)
  2. BYPASS FILE  — /tmp/claude-hook-bypass contains CONFIRMED within 300s → allow

Fail-open: any exception, missing transcript, malformed JSON → allow.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "plan-guard-off"
BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
BYPASS_TOKEN = "CONFIRMED"

BASH_STREAK_LIMIT = 3  # block on the (LIMIT+1)th consecutive Bash call


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
    return bool(content) and content.split()[0] == BYPASS_TOKEN


def scan_transcript(path: str) -> dict:
    """Return bash_streak (consecutive Bash at tail) and todo_write_count."""
    tool_calls: list[str] = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if o.get("type") != "assistant":
                    continue
                for item in (o.get("message") or {}).get("content") or []:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_calls.append(item.get("name", ""))
    except (FileNotFoundError, PermissionError, OSError):
        return {"bash_streak": 0, "todo_write_count": 0}

    todo_write_count = sum(1 for t in tool_calls if t == "TodoWrite")
    bash_streak = 0
    for tool in reversed(tool_calls):
        if tool == "Bash":
            bash_streak += 1
        else:
            break
    return {"bash_streak": bash_streak, "todo_write_count": todo_write_count}


def decide(scan: dict, kill: bool, bypass: bool) -> dict:
    if kill:
        return {"decision": "allow", "level": "kill"}
    if bypass:
        return {"decision": "allow", "level": "bypass"}
    if scan["bash_streak"] >= BASH_STREAK_LIMIT and scan["todo_write_count"] == 0:
        return {
            "decision": "deny",
            "level": "hard",
            "reason": (
                f"PLAN-FIRST: {scan['bash_streak']} consecutive Bash calls with no plan. "
                f"Stop. Use TodoWrite to list your steps before running more commands. "
                f"Bypass (5 min): echo CONFIRMED > /tmp/claude-hook-bypass"
            ),
        }
    return {"decision": "allow", "level": "ok"}


def emit_context(message: str) -> None:
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
            return 0

        transcript_path = payload.get("transcript_path", "")
        if not transcript_path:
            return 0

        scan = scan_transcript(transcript_path)
        result = decide(scan, kill=kill_switch_active(), bypass=bypass_active())

        if result["decision"] == "deny":
            print(result["reason"], file=sys.stderr)
            return 2

        if result["level"] == "kill":
            emit_context(f"PLAN-FIRST guard: kill switch on ({KILL_SWITCH}).")
        elif result["level"] == "bypass":
            emit_context(f"PLAN-FIRST guard: bypass active.")

        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
