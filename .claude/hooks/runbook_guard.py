#!/usr/bin/env python3
"""Force `lookup_runbook` before any operational `mcp__ops__*` tool call.

The static analyzer `tests/runbook_compliance.py` detects `runbook_missed` /
`runbook_late` *after* the fact. This hook enforces the same policy *before*
the tool call runs, so the agent cannot skip the runbook even once.

Wired as PreToolUse with matcher `mcp__ops__.*`. Coexists with block-ssh.py
(Bash) and budget_guard.py (*) — PreToolUse hooks run in declaration order.

Policy:
    operational mcp__ops__ tool  +  no prior lookup_runbook in transcript → exit 2
    exempt tool                                                          → allow
    lookup_runbook already seen                                          → allow

Exempt tools (kept in sync with tests/runbook_compliance.py RUNBOOK_EXEMPT_TOOLS):
    mcp__ops__lookup_runbook
    mcp__ops__read_doc
    mcp__ops__record_runbook_outcome
    mcp__ops__ai_cost_summary

Escape hatches (checked BEFORE policy, in this order):

  1. KILL SWITCH — `~/.ops-mcp/runbook-guard-off` exists → exit 0 immediately.
     No TTL. Reliable escape if the enforcement itself misbehaves.

     Toggle: `touch ~/.ops-mcp/runbook-guard-off`   # off
             `rm ~/.ops-mcp/runbook-guard-off`      # on

  2. BYPASS FILE — `/tmp/claude-hook-bypass` whose first whitespace-delimited
     token is "CONFIRMED", mtime within 300s. Identical parsing to the other
     hooks so one bypass write unlocks all three.

Fail-open invariants (mirrors block-ssh / budget_guard):
    - Malformed stdin JSON              → exit 0
    - Missing transcript_path           → exit 0
    - Missing transcript file           → exit 0
    - Malformed line in transcript      → skipped, others counted
    - Non-ops tool name                 → exit 0
    - Unhandled exception               → exit 0 (never lock out)

Exit codes:
    0 = allow    2 = block (stderr carries the instruction)
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "runbook-guard-off"
BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
BYPASS_TOKEN = "CONFIRMED"

RUNBOOK_TOOL = "mcp__ops__lookup_runbook"
RUNBOOK_EXEMPT_TOOLS = frozenset({
    RUNBOOK_TOOL,
    "mcp__ops__read_doc",
    "mcp__ops__record_runbook_outcome",
    "mcp__ops__ai_cost_summary",
})
OPS_PREFIX = "mcp__ops__"


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


def transcript_has_runbook(path: str) -> bool:
    """Return True if any assistant tool_use with name == RUNBOOK_TOOL exists."""
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
                msg = o.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") == RUNBOOK_TOOL:
                        return True
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError):
        return False
    return False


def decide(tool_name: str, transcript_path: str, kill: bool, bypass: bool) -> dict:
    """Pure decision. Precedence: kill > bypass > non-ops > exempt > runbook-present > block."""
    if kill:
        return {"decision": "allow", "level": "kill"}
    if bypass:
        return {"decision": "allow", "level": "bypass"}
    if not tool_name.startswith(OPS_PREFIX):
        return {"decision": "allow", "level": "non-ops"}
    if tool_name in RUNBOOK_EXEMPT_TOOLS:
        return {"decision": "allow", "level": "exempt"}
    if transcript_path and transcript_has_runbook(transcript_path):
        return {"decision": "allow", "level": "runbook-ok"}
    return {
        "decision": "block",
        "level": "hard",
        "reason": (
            f"RUNBOOK-FIRST: `{tool_name}` is an operational ops tool but "
            f"`lookup_runbook` has not been called in this session. "
            f"Call `mcp__ops__lookup_runbook(problem_description=\"<intent or symptom>\")` "
            f"first, then retry. Exempt tools you may use before lookup: "
            f"read_doc, record_runbook_outcome, ai_cost_summary. "
            f"To lift this hook: `touch ~/.ops-mcp/runbook-guard-off`  (or "
            f"write 'CONFIRMED' to /tmp/claude-hook-bypass for 5 min)."
        ),
    }


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

        tool_name = payload.get("tool_name") or ""
        transcript_path = payload.get("transcript_path") or ""

        result = decide(
            tool_name,
            transcript_path,
            kill=kill_switch_active(),
            bypass=bypass_active(),
        )

        if result["decision"] == "block":
            print(result["reason"], file=sys.stderr)
            return 2

        level = result.get("level")
        if level == "bypass":
            emit_pre_tool_use_context(
                f"RUNBOOK-GUARD BYPASS active ({BYPASS_FILE}). TTL {BYPASS_TTL_SEC}s."
            )
        elif level == "kill":
            emit_pre_tool_use_context(
                f"RUNBOOK-GUARD KILL SWITCH on ({KILL_SWITCH}). Hook fully disabled."
            )
        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
