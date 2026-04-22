#!/usr/bin/env python3
"""Session-wide token + time budget guard.

Complements the in-process server guards (thrash_guard, payload_similarity_guard
in server/guards.py) which catch *patterns* of waste at the MCP layer. This hook
catches *cumulative* waste at the Claude Code layer — the case where each
individual tool call is reasonable but the session as a whole has burned too
much time or too many output tokens. It also covers tools the MCP guards
cannot see (Read, Edit, Write, Bash, WebFetch, etc.).

Wired as PreToolUse with matcher "mcp__ops__.*|Agent|Bash|WebFetch|WebSearch".
Skips cheap local ops (Read/Edit/Write/Glob/Grep) to reduce subprocess overhead.
Coexists with block-ssh.py (Bash matcher) — PreToolUse hooks run in declaration order.

Caps:
    BUDGET_TIME_MIN      env override, default 30      (minutes from first event)
    BUDGET_TOKEN_OUTPUT  env override, default 100000  (output tokens; cache excluded)

Behavior:
    < 50% of either cap   → silent allow
    >= 50% of either cap  → allow with hookSpecificOutput.additionalContext warn
    >= 100% of either cap → exit 2 with stderr deny — model sees a stop directive

Escape hatches (checked BEFORE caps, in this order):

  1. KILL SWITCH — `~/.ops-mcp/budget-off` exists → exit 0 immediately. No TTL,
     no content match, no clock games. Presence = off. This is the reliable
     escape if the cap mechanism itself misbehaves.

     Toggle: `touch ~/.ops-mcp/budget-off`     # off
             `rm ~/.ops-mcp/budget-off`        # on

  2. BYPASS FILE — `/tmp/claude-hook-bypass` whose first whitespace-delimited
     token is "CONFIRMED", mtime within 300s. Same mechanism as block-ssh.py;
     loosened from exact-match to first-token so pasted commands with trailing
     comments still work. 300-second TTL.

Fail-open invariants:
    - Missing transcript_path                        → exit 0 (no-op allow)
    - Malformed stdin JSON                           → exit 0 (no-op allow)
    - Missing transcript file                        → exit 0 (zero tally)
    - Malformed line in transcript                   → skipped, others counted
    - Non-int / zero / negative cap env var          → fall back to default
    - Unhandled exception anywhere in main           → exit 0 (never lock out)
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "budget-off"
BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
BYPASS_TOKEN = "CONFIRMED"

DEFAULT_TIME_CAP_MIN = 30
DEFAULT_TOKEN_CAP = 100_000


def kill_switch_active() -> bool:
    """Simple presence check — no TTL, no content. Cannot misbehave."""
    return KILL_SWITCH.exists()


def bypass_active() -> bool:
    """Time-limited bypass; first whitespace-delimited token must be CONFIRMED."""
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


def tally_transcript(path: str) -> dict:
    """Sum output tokens and bracket timestamps from a Claude Code transcript JSONL.

    Cache reads/creates are intentionally excluded — counting them would punish
    legitimate long-context work. Per-line errors (bad JSON, bad usage value
    types) are skipped individually so one malformed event cannot break the
    whole tally.
    """
    out = 0
    first_ts: str | None = None
    last_ts: str | None = None
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
                ts = o.get("timestamp")
                if isinstance(ts, str):
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts
                if o.get("type") == "assistant":
                    msg = o.get("message") or {}
                    u = msg.get("usage") or {}
                    raw = u.get("output_tokens")
                    try:
                        out += int(raw or 0)
                    except (TypeError, ValueError):
                        # Non-numeric usage values are skipped; tally continues.
                        continue
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError):
        return {"output_tokens": 0, "first_ts": None, "last_ts": None}
    return {"output_tokens": out, "first_ts": first_ts, "last_ts": last_ts}


def parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError, TypeError):
        return None


def positive_int_env(name: str, default: int) -> int:
    """Return env-var int if it parses AND is > 0; otherwise the default."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return default
    return v if v > 0 else default


def decide(
    tally: dict,
    now_ts: float,
    time_cap_min: int,
    token_cap: int,
    kill: bool,
    bypass: bool,
) -> dict:
    """Pure decision function.

    Returns {decision, level, [reason]}. Order of precedence: kill > bypass > caps.
    """
    if kill:
        return {"decision": "allow", "level": "kill"}
    if bypass:
        return {"decision": "allow", "level": "bypass"}

    out = int(tally.get("output_tokens") or 0)
    first = parse_iso(tally.get("first_ts"))
    elapsed_min = (now_ts - first) / 60.0 if first else 0.0

    if out >= token_cap:
        return {
            "decision": "deny",
            "level": "hard",
            "reason": (
                f"BUDGET EXCEEDED: {out:,} output tokens >= cap {token_cap:,}. "
                f"STOP. Summarize what you've done and what remains, then return "
                f"control to the user. To continue, ask explicitly — do not retry. "
                f"User can lift via: touch ~/.ops-mcp/budget-off  (or raise "
                f"BUDGET_TOKEN_OUTPUT and relaunch)."
            ),
        }
    if elapsed_min >= time_cap_min:
        return {
            "decision": "deny",
            "level": "hard",
            "reason": (
                f"BUDGET EXCEEDED: {elapsed_min:.1f} min elapsed >= cap {time_cap_min} min. "
                f"STOP. Summarize what you've done and what remains, then return "
                f"control to the user. To continue, ask explicitly — do not retry. "
                f"User can lift via: touch ~/.ops-mcp/budget-off  (or raise "
                f"BUDGET_TIME_MIN and relaunch)."
            ),
        }

    half_tok = token_cap // 2
    half_min = time_cap_min / 2.0
    if out >= half_tok or elapsed_min >= half_min:
        return {
            "decision": "allow",
            "level": "warn",
            "reason": (
                f"BUDGET WARN: {out:,}/{token_cap:,} output tokens, "
                f"{elapsed_min:.1f}/{time_cap_min} min elapsed. Wrap up soon."
            ),
        }

    return {"decision": "allow", "level": "ok"}


def emit_pre_tool_use_context(message: str) -> None:
    """Emit a PreToolUse-shaped JSON envelope so the model sees the message.

    Per Claude Code hooks spec, PreToolUse extra context must live inside
    hookSpecificOutput with hookEventName: 'PreToolUse'. Top-level
    additionalContext is for UserPromptSubmit only.
    """
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

        transcript_path = payload.get("transcript_path", "")
        if not transcript_path:
            return 0

        time_cap = positive_int_env("BUDGET_TIME_MIN", DEFAULT_TIME_CAP_MIN)
        token_cap = positive_int_env("BUDGET_TOKEN_OUTPUT", DEFAULT_TOKEN_CAP)

        tally = tally_transcript(transcript_path)
        result = decide(
            tally,
            now_ts=time.time(),
            time_cap_min=time_cap,
            token_cap=token_cap,
            kill=kill_switch_active(),
            bypass=bypass_active(),
        )

        if result["decision"] == "deny":
            print(result["reason"], file=sys.stderr)
            return 2

        level = result.get("level")
        if level == "warn":
            emit_pre_tool_use_context(result["reason"])
        elif level == "bypass":
            emit_pre_tool_use_context(
                f"BUDGET BYPASS active ({BYPASS_FILE}). Caps disabled until file "
                f"expires (TTL {BYPASS_TTL_SEC}s) — finish carefully and stop."
            )
        elif level == "kill":
            emit_pre_tool_use_context(
                f"BUDGET KILL SWITCH on ({KILL_SWITCH}). Caps fully disabled."
            )
        return 0

    except Exception:
        # Last-resort fail-open. Log to stderr for the user but don't block.
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
