"""Pure-Python guard functions for ops-mcp tools.

Kept in a separate module (no MCP / yaml / subprocess deps) so they can be
unit-tested directly without booting the full server.
"""
from __future__ import annotations

import hashlib
import json

# ── Anti-thrash guard ─────────────────────────────────────────────────────────
#
# When the same (tool, target) is called repeatedly in a row, the caller is
# almost always spiraling — diagnosing without a plan. Return a hard STOP
# payload so the agent has to break the loop (consult the runbook, state
# intent, ask the user). Historical evidence: session 17e3bfde fired 16
# consecutive wp_cli calls on ksm-wp that never converged.
#
# FastMCP spawns one server process per stdio client, so module-global
# state on the calling server.py is effectively per-session.

_THRASH_WINDOW: list[tuple[str, str]] = []
_THRASH_WINDOW_MAX = 20
THRASH_LIMIT = 5


def reset_thrash_window() -> None:
    _THRASH_WINDOW.clear()


def thrash_guard(tool: str, target: str | None) -> dict | None:
    """Record this call and return a stop payload if it's the Nth consecutive identical one."""
    key = (tool, target or "")
    _THRASH_WINDOW.insert(0, key)
    del _THRASH_WINDOW[_THRASH_WINDOW_MAX:]
    run = 1
    for k in _THRASH_WINDOW[1:]:
        if k == key:
            run += 1
        else:
            break
    if run >= THRASH_LIMIT:
        return {
            "ok": False,
            "error": "thrash_stop",
            "tool": tool,
            "target": target,
            "consecutive_calls": run,
            "message": (
                f"You have called {tool} on {target!r} {run} times in a row without progress. "
                f"Stop. Reassess. Options: (1) call lookup_runbook for this problem, "
                f"(2) state what specific signal you're looking for, "
                f"(3) ask the user. "
                f"Any different tool call breaks the thrash counter."
            ),
        }
    return None


# ── Runbook hygiene guards ────────────────────────────────────────────────────
#
# Rabbit-holes happen when lookup_runbook returns:
#   1. Weakly-matching entries (single-keyword overlap with an unrelated problem).
#   2. Two top-scoring entries with contradictory resolutions — the agent
#      has no basis to pick and oscillates.
#
# These two functions filter/annotate the result list before it's returned.

RUNBOOK_MIN_SCORE = 2


def _resolution_key(entry: dict) -> str:
    """Canonical fingerprint of an entry's suggested fix."""
    if entry.get("source") == "ai-agent":
        steps = entry.get("resolution_steps") or []
        return "\n".join(str(s) for s in steps)
    res = entry.get("resolution") or {}
    return json.dumps(res, sort_keys=True)


def filter_weak_matches(
    results: list[dict], min_score: int = RUNBOOK_MIN_SCORE
) -> list[dict]:
    """Drop entries below min_score; fall back to best single match if none qualify."""
    strong = [r for r in results if r.get("match_score", 0) >= min_score]
    if strong:
        return strong
    return results[:1]


def flag_runbook_conflicts(results: list[dict]) -> list[dict]:
    """If top-tier entries share a match_score but disagree on the fix, flag conflict.

    Conflicting entries lose auto_executable — caller must pick or ask the user.
    """
    if len(results) < 2:
        return results
    top_score = results[0].get("match_score", 0)
    tier = [r for r in results if r.get("match_score", 0) == top_score]
    if len(tier) < 2:
        return results
    if len({_resolution_key(r) for r in tier}) > 1:
        for r in results:
            if r.get("match_score", 0) == top_score:
                r["conflict"] = True
                r["auto_executable"] = False
    return results


# ── Payload similarity guard ──────────────────────────────────────────────────
#
# Catches the token-waste thrash mode observed on 2026-04-20: the same large
# blob coming back out of read_file and going straight into write_file — a
# remote→remote paste that git_sync solves in one call.
#
# The MCP server's surface includes read_file and write_file (the two tools
# that can shuttle significant content); client-side Bash never reaches this
# guard. So PAYLOAD_SIM_LIMIT=2 is the honest threshold: a >=8KB blob that
# appears in both read_file and write_file within the recent window is the
# pattern we want to stop. thrash_guard covers the single-tool repeat case.

_PAYLOAD_WINDOW: list[tuple[str, str]] = []
_PAYLOAD_WINDOW_MAX = 10
PAYLOAD_SIM_LIMIT = 2
PAYLOAD_MIN_BYTES = 8 * 1024


def reset_payload_window() -> None:
    _PAYLOAD_WINDOW.clear()


def _payload_hash(content) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8", errors="ignore")
    elif not isinstance(content, (bytes, bytearray)):
        return ""
    if len(content) < PAYLOAD_MIN_BYTES:
        return ""
    return hashlib.sha256(content[:4096]).hexdigest()[:16]


def payload_similarity_guard(tool: str, content) -> dict | None:
    """Record this payload's hash; stop if the same large blob appears across
    PAYLOAD_SIM_LIMIT distinct tools in the recent window.
    """
    h = _payload_hash(content)
    if not h:
        return None
    _PAYLOAD_WINDOW.insert(0, (tool, h))
    del _PAYLOAD_WINDOW[_PAYLOAD_WINDOW_MAX:]
    tools_with_hash = {t for t, hh in _PAYLOAD_WINDOW if hh == h}
    if len(tools_with_hash) >= PAYLOAD_SIM_LIMIT:
        return {
            "ok": False,
            "error": "payload_thrash_stop",
            "distinct_tools": sorted(tools_with_hash),
            "hash": h,
            "message": (
                f"The same >={PAYLOAD_MIN_BYTES // 1024}KB payload moved through "
                f"{len(tools_with_hash)} distinct tools ({sorted(tools_with_hash)}). "
                f"This is token-waste thrash. Use a direct-transfer path "
                f"(git_sync, bootstrap_git) instead of shuttling content."
            ),
        }
    return None
