#!/usr/bin/env python3
"""Block WebFetch on YouTube URLs — force yt-dlp transcript download instead.

Intent: WebFetch returns YouTube page chrome (footer nav), never the transcript.
Stephan has repeatedly corrected this. The canonical method is `yt-dlp
--write-auto-sub --skip-download`. See
memory/feedback_youtube_transcripts_via_ytdlp.md.

Escape hatches (mirrors block-ssh.py / budget_guard.py / runbook_guard.py):

  1. KILL SWITCH — `~/.ops-mcp/youtube-guard-off` exists → exit 0 immediately.
     Toggle: `touch ~/.ops-mcp/youtube-guard-off`   # off
             `rm ~/.ops-mcp/youtube-guard-off`      # on

  2. BYPASS FILE — `/tmp/claude-hook-bypass` first token == "CONFIRMED",
     mtime within 300s. Same parsing as the other hooks.

Fail-open invariants:
    - Malformed stdin JSON   → exit 0
    - Missing tool_input.url → exit 0
    - Non-YouTube URL        → exit 0
    - Unhandled exception    → exit 0

Exit codes: 0 = allow, 2 = block (stderr carries the reason).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

KILL_SWITCH = Path.home() / ".ops-mcp" / "youtube-guard-off"
BYPASS_FILE = "/tmp/claude-hook-bypass"
BYPASS_TTL_SEC = 300
BYPASS_TOKEN = "CONFIRMED"

YOUTUBE_HOST_RE = re.compile(
    r"^(?:https?://)?"
    r"(?:[\w-]+\.)*"
    r"(?:youtube\.com|youtu\.be|youtube-nocookie\.com)"
    r"(?:/|$)",
    re.IGNORECASE,
)


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


def is_youtube_url(url: str) -> bool:
    return bool(url) and bool(YOUTUBE_HOST_RE.match(url.strip()))


def decide(url: str, kill: bool, bypass: bool) -> dict:
    """Pure decision. Precedence: kill > bypass > youtube-match."""
    if kill:
        return {"decision": "allow", "level": "kill"}
    if bypass:
        return {"decision": "allow", "level": "bypass"}
    if is_youtube_url(url):
        return {
            "decision": "block",
            "level": "hard",
            "reason": (
                f"WebFetch on YouTube URL ({url!r}) returns page chrome, not the "
                "transcript. Use yt-dlp instead:\n\n"
                '  cd /tmp && yt-dlp --write-auto-sub --write-sub --sub-lang en \\\n'
                '    --skip-download --sub-format vtt -o "yt-%(id)s.%(ext)s" "<URL>"\n\n'
                "Then dedupe VTT to plain text (rolling auto-caption duplicates) "
                "and Read the .txt. Full recipe: "
                "memory/feedback_youtube_transcripts_via_ytdlp.md.\n\n"
                "To lift this hook: `touch ~/.ops-mcp/youtube-guard-off`  (or "
                "write 'CONFIRMED' to /tmp/claude-hook-bypass for 5 min)."
            ),
        }
    return {"decision": "allow", "level": "ok"}


def emit_pre_tool_use_context(message: str) -> None:
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
        url = payload.get("tool_input", {}).get("url", "")

        result = decide(
            url,
            kill=kill_switch_active(),
            bypass=bypass_active(),
        )

        if result["decision"] == "block":
            print(result["reason"], file=sys.stderr)
            return 2

        level = result.get("level")
        if level == "bypass":
            emit_pre_tool_use_context(
                f"YOUTUBE-GUARD BYPASS active ({BYPASS_FILE}). TTL {BYPASS_TTL_SEC}s."
            )
        elif level == "kill":
            emit_pre_tool_use_context(
                f"YOUTUBE-GUARD KILL SWITCH on ({KILL_SWITCH}). Hook fully disabled."
            )
        return 0

    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
