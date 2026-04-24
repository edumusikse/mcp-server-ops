#!/usr/bin/env python3
"""Block assistant from stopping when it uses completion language without verification evidence.

Stephan has said hundreds of times: never claim done without verifying. This hook
fires on Stop and scans the last assistant message for trigger phrases. If found
without a verification signal, it blocks the stop and demands evidence.

Trigger phrases: "done", "fixed", "finished", "complete", "should work",
"should now", "deployed", "I've", "it's working", "the fix is"

Verification signals (any of these in the last assistant turn satisfies the check):
- HTTP status code in response (200, 301, 302, etc.)
- grep output with a line:column result
- curl command with a result
- "OK" from a tee/ssh command
- explicit "verified" or "confirmed" followed by evidence

Escape hatch: `~/.ops-mcp/verify-guard-off` exists → exit 0 immediately.

Fail-open: any exception → exit 0 (never lock out).
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "verify-guard-off"

TRIGGER_PHRASES = [
    r"\bdone\b",
    r"\bfixed\b",
    r"\bfinished\b",
    r"\bcomplete[d]?\b",
    r"should work",
    r"should now",
    r"\bdeployed\b",
    r"the fix is",
    r"it'?s working",
    r"fix works",
    r"fix is working",
]

# Evidence that real verification happened
VERIFICATION_SIGNALS = [
    r"\b(200|301|302|404|500)\b.*HTTP",
    r"HTTP.*\b(200|301|302|404|500)\b",
    r"class=\"postbox\s*\"",      # WP metabox visible
    r"sudo grep.*:\s*\d+",        # grep with line number result
    r"\bOK\b",                    # tee/ssh success
    r'verified\b.*\n.*\n',        # "verified" with content after
    r"confirmed.*line \d+",
    r"\d+ lines? analysed",       # tail_logs result
    r'"ok":\s*true',              # MCP tool success
]

BLOCK_MESSAGE = (
    "VERIFY-BEFORE-DONE: Your response contains completion language "
    "('done', 'fixed', 'deployed', 'should work', etc.) but no verification "
    "evidence is visible in this turn. Before stopping:\n"
    "  1. Run a live check (curl, grep on server, MCP tool result)\n"
    "  2. Show the actual output in your response\n"
    "  3. Then and only then state it is done\n\n"
    "To disable this guard: touch ~/.ops-mcp/verify-guard-off"
)


def get_last_assistant_turn(transcript_path: str) -> tuple[str, bool]:
    """Return (text, had_tool_use) for the last assistant message in the transcript."""
    last_text = ""
    last_had_tools = False
    try:
        with open(transcript_path) as f:
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
                msg = o.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                parts = []
                had_tools = False
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        parts.append(block.get("text") or "")
                    elif block.get("type") == "tool_use":
                        had_tools = True
                if parts:
                    last_text = " ".join(parts)
                    last_had_tools = had_tools
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return last_text, last_had_tools


def has_trigger(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in TRIGGER_PHRASES)


def has_verification(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in VERIFICATION_SIGNALS)


def main() -> int:
    try:
        if KILL_SWITCH.exists():
            return 0

        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            return 0

        transcript_path = payload.get("transcript_path") or ""
        if not transcript_path:
            return 0

        text, had_tool_use = get_last_assistant_turn(transcript_path)
        if not text:
            return 0

        # Only check for completion language if operational work was done this turn.
        # Pure conversational/editorial responses have nothing to verify.
        if not had_tool_use:
            return 0

        if has_trigger(text) and not has_verification(text):
            print(BLOCK_MESSAGE, file=sys.stderr)
            return 2

        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
