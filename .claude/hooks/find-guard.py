#!/usr/bin/env python3
"""PreToolUse hook: intercept find/grep-r commands and inject the known-paths reference.

When a Bash command contains 'find ' or 'grep -r', injects .claude/known-paths.md
as additionalContext so the model sees documented paths before running the search.
If the path is already there, the model should use it directly instead of searching.

After a find returns new paths, the model is reminded to document them.

Fail-open: any exception → exit 0 (never block work).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

KNOWN_PATHS = Path(__file__).parent.parent / "known-paths.md"


def is_search_command(cmd: str) -> bool:
    triggers = ["find ", "grep -r", "grep -rl", "grep -rn"]
    return any(t in cmd for t in triggers)


def main() -> None:
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")

        if not is_search_command(command):
            sys.exit(0)

        if not KNOWN_PATHS.exists():
            sys.exit(0)

        known = KNOWN_PATHS.read_text()
        context = (
            "STOP — check known-paths.md before running this search. "
            "If the path is already documented below, use it directly instead of running find/grep.\n"
            "If the search reveals new paths, add them to .claude/known-paths.md before continuing.\n\n"
            + known
        )
        print(json.dumps({"hookSpecificOutput": {"additionalContext": context}}))
        sys.exit(0)
    except Exception:
        sys.exit(0)


main()
