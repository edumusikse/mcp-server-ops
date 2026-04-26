#!/usr/bin/env python3
"""PostToolUse hook: force attention to any mcp__ops__* ok=false result.

When an ops MCP tool returns {"ok": false, ...}, inject a hard-stop message
into Claude's context so the error is addressed before proceeding.

Fail-open: any exception → silent exit 0 (never locks a session).
"""
from __future__ import annotations

import json
import sys
import traceback


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    try:
        response = data.get("response", {})
        tool_name = data.get("tool_name", "unknown")

        if isinstance(response, str):
            try:
                response = json.loads(response)
            except (json.JSONDecodeError, ValueError):
                return 0

        if not isinstance(response, dict):
            return 0

        if response.get("ok") is not False:
            return 0

        error = response.get("error", "unknown error")
        message = response.get("message", "")

        lines = [
            f"TOOL FAILURE — {tool_name} returned ok=false.",
            f"Error: {error}",
        ]
        if message:
            lines.append(f"Detail: {message[:300]}")
        lines.append(
            "Fix this before your next tool call: "
            "wrong field/name → correct it; permission denied → use sudo=True or the right path; "
            "thrash_stop → break with tail_logs or read_file first."
        )

        print(json.dumps({"additionalContext": "\n".join(lines)}))
        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
