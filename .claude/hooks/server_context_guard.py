#!/usr/bin/env python3
"""Force /server skill invocation at every session start in the ops-agent workspace.

Skipping the /server skill has caused repeated failures: wrong deploy paths,
missing plugin context, no ops-map, no rules loaded. This hook makes loading
mandatory by injecting a CRITICAL instruction at SessionStart that is impossible
to miss.

Escape hatch: `~/.ops-mcp/server-context-guard-off` exists → inject nothing.

Fail-open: any exception → exit 0, print nothing.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "server-context-guard-off"

INSTRUCTION = """\
## MANDATORY: Load server context NOW

This is the ops-agent server workspace. Before responding to ANY user request, \
you MUST invoke the /server skill as your first action.

Invoke it by calling: Skill(skill="server")

The /server skill loads: fleet_status, read_doc("ops-map"), read_doc("rules"), \
read_doc("guard-rules"), and lookup_runbook. Without this:
- You will not know the correct deploy paths for WP mu-plugins
- You will not know which MCP tools to use vs which are blocked
- You will not have the rules that prevent repeated operational failures

DO NOT skip this. DO NOT assume you already know the context. INVOKE /server NOW \
as your first action, then respond to the user.
"""


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
        emit(INSTRUCTION)
        return 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
