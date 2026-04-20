#!/usr/bin/env python3
"""Session-wide token + time budget guard.

Complements the in-process server guards (thrash_guard, payload_similarity_guard
in server/guards.py) which catch *patterns* of waste at the MCP layer. This hook
catches *cumulative* waste at the Claude Code layer — the case where each
individual tool call is reasonable but the session as a whole has burned too
much time or too many output tokens. It also covers tools the MCP guards
cannot see (Read, Edit, Write, Bash, WebFetch, etc.).

Wired as PreToolUse with matcher "*". Coexists with block-ssh.py (Bash matcher)
— PreToolUse hooks run in declaration order, both are advisory until exit 2.

Caps:
    BUDGET_TIME_MIN      env override, default 30  (minutes from first assistant message)
    BUDGET_TOKEN_OUTPUT  env override, default 100000  (output tokens; cache reads excluded)

Behavior:
    < 50% of either cap   → silent allow
    >= 50% of either cap  → allow with additionalContext warn (visible to model)
    >= 100% of either cap → exit 2 with stderr deny — model sees a stop directive

Bypass: write 'CONFIRMED' to /tmp/claude-hook-bypass (TTL 300s). Same mechanism
as block-ssh.py — uniform emergency path documented in ~/EMERGENCY-CLAUDE-HOOK-BYPASS.md.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
DEFAULT_TIME_CAP_MIN = 30
DEFAULT_TOKEN_CAP = 100_000


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


def tally_transcript(path: str) -> dict:
    """Sum output tokens and bracket timestamps from a Claude Code transcript JSONL.

    Cache reads/creates are intentionally excluded — they are cheap and counting
    them would trip the cap on legitimate long-context work.
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
                if ts and isinstance(ts, str):
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts
                if o.get("type") == "assistant":
                    msg = o.get("message") or {}
                    u = msg.get("usage") or {}
                    out += int(u.get("output_tokens") or 0)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return {"output_tokens": 0, "first_ts": None, "last_ts": None}
    return {"output_tokens": out, "first_ts": first_ts, "last_ts": last_ts}


def parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError, TypeError):
        return None


def decide(
    tally: dict,
    now_ts: float,
    time_cap_min: int,
    token_cap: int,
    bypass: bool,
) -> dict:
    """Pure decision function — returns {decision, level, [reason]}."""
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
                f"control to the user. To continue, ask explicitly — do not retry."
            ),
        }
    if elapsed_min >= time_cap_min:
        return {
            "decision": "deny",
            "level": "hard",
            "reason": (
                f"BUDGET EXCEEDED: {elapsed_min:.1f} min elapsed >= cap {time_cap_min} min. "
                f"STOP. Summarize what you've done and what remains, then return "
                f"control to the user. To continue, ask explicitly — do not retry."
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed payload: don't block the session

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return 0

    try:
        time_cap = int(os.environ.get("BUDGET_TIME_MIN", DEFAULT_TIME_CAP_MIN))
        token_cap = int(os.environ.get("BUDGET_TOKEN_OUTPUT", DEFAULT_TOKEN_CAP))
    except ValueError:
        time_cap, token_cap = DEFAULT_TIME_CAP_MIN, DEFAULT_TOKEN_CAP

    tally = tally_transcript(transcript_path)
    result = decide(tally, time.time(), time_cap, token_cap, bypass_active())

    if result["decision"] == "deny":
        print(result["reason"], file=sys.stderr)
        return 2

    if result.get("level") == "warn":
        # additionalContext is visible to the model on PreToolUse allow.
        print(json.dumps({
            "continue": True,
            "additionalContext": result["reason"],
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
