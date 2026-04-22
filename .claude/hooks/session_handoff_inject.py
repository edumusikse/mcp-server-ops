#!/usr/bin/env python3
"""Inject the latest session handoff into a new session's context.

Intent: Stephan repeatedly asks for summaries and gets frustrated when the
next session doesn't read them. This SessionStart hook makes the handoff
*unskippable* — its content is injected as additionalContext, which lands
in the conversation system prompt and cannot be missed.

Handoff file: `<project>/.claude/handoffs/LATEST.md`
    Produced by the `/session-handoff` skill. Always overwritten atomically
    so "the latest one" is well-defined.

Injection rules:
    - File missing                         → silent no-op (fresh project)
    - File present, mtime within 14 days   → inject full content
    - File older than 14 days              → inject a one-liner pointer
                                             (stale, don't trust blindly)

Escape hatch:
    `~/.ops-mcp/session-handoff-off` exists → inject nothing.
    (Kept symmetrical with the other hooks. No TTL, no bypass file — this
    hook is additive, never blocks anything.)

Fail-open: any exception → exit 0, print nothing.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
HANDOFF_PATH = PROJECT_DIR / ".claude" / "handoffs" / "LATEST.md"
KILL_SWITCH = Path.home() / ".ops-mcp" / "session-handoff-off"
FRESH_MAX_SEC = 14 * 24 * 3600


def emit(message: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": message,
        }
    }))


def main() -> int:
    try:
        if KILL_SWITCH.exists():
            return 0
        if not HANDOFF_PATH.exists():
            return 0
        age = time.time() - HANDOFF_PATH.stat().st_mtime
        content = HANDOFF_PATH.read_text(errors="replace").strip()
        if not content:
            return 0
        age_days = int(age // 86400)
        if age < FRESH_MAX_SEC:
            emit(
                f"## Last session handoff (from {HANDOFF_PATH}, ~{age_days}d old)\n\n"
                "READ THIS BEFORE TAKING ANY ACTION. Treat it as current state, "
                "but verify specifics against the repo before acting on them.\n\n"
                f"---\n\n{content}\n\n---\n\n"
                "Produced by the `/session-handoff` skill. Run that skill before "
                "this session ends to refresh it."
            )
        else:
            emit(
                f"Stale handoff at {HANDOFF_PATH} ({age_days}d old) — likely "
                "out of date, do not rely on it. Ignore unless the user refers "
                "to it."
            )
        return 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
