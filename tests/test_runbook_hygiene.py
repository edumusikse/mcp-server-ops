#!/usr/bin/env python3
"""Unit tests for runbook match-hygiene guards.

Tests the pure-Python filter + conflict-detection logic without booting the
MCP server or touching SQLite.
Run: `python3 tests/test_runbook_hygiene.py`
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from guards import filter_weak_matches, flag_runbook_conflicts  # noqa: E402

failures: list[str] = []


def assert_eq(actual, expected, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


# ── filter_weak_matches ──────────────────────────────────────────────────────

# Case 1: score=1 entries dropped when a score>=2 entry exists.
r = filter_weak_matches([
    {"match_score": 2, "source": "ai-agent", "resolution_steps": ["a"]},
    {"match_score": 1, "source": "ai-agent", "resolution_steps": ["b"]},
])
assert_eq(len(r), 1, "drop score=1 when score=2 exists")
assert_eq(r[0]["match_score"], 2, "kept the score=2 entry")

# Case 2: all entries below threshold → fallback to best single.
r = filter_weak_matches([
    {"match_score": 1, "source": "ai-agent", "resolution_steps": ["a"]},
    {"match_score": 1, "source": "ai-agent", "resolution_steps": ["b"]},
])
assert_eq(len(r), 1, "fallback to best single when all weak")

# Case 3: empty input → empty output.
r = filter_weak_matches([])
assert_eq(r, [], "empty in → empty out")

# ── flag_runbook_conflicts ───────────────────────────────────────────────────

# Case 4: tied score, different resolutions → both flagged, auto_executable cleared.
entries = [
    {"match_score": 3, "source": "ai-agent", "resolution_steps": ["fix-A"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
    {"match_score": 3, "source": "ai-agent", "resolution_steps": ["fix-B"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
]
r = flag_runbook_conflicts(entries)
assert_eq(r[0].get("conflict"), True, "top-tier entry 0 flagged conflict")
assert_eq(r[1].get("conflict"), True, "top-tier entry 1 flagged conflict")
assert_eq(r[0]["auto_executable"], False, "conflict clears auto_executable on 0")
assert_eq(r[1]["auto_executable"], False, "conflict clears auto_executable on 1")

# Case 5: tied score, same resolution → no conflict.
entries = [
    {"match_score": 3, "source": "ai-agent", "resolution_steps": ["fix"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
    {"match_score": 3, "source": "ai-agent", "resolution_steps": ["fix"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
]
r = flag_runbook_conflicts(entries)
assert_eq(r[0].get("conflict"), None, "same resolution → not flagged")
assert_eq(r[0]["auto_executable"], True, "auto_executable preserved")

# Case 6: clear winner (different scores) → no conflict even with disagreement.
entries = [
    {"match_score": 3, "source": "ai-agent", "resolution_steps": ["fix-A"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
    {"match_score": 2, "source": "ai-agent", "resolution_steps": ["fix-B"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
]
r = flag_runbook_conflicts(entries)
assert_eq(r[0].get("conflict"), None, "clear winner not flagged")
assert_eq(r[0]["auto_executable"], True, "winner keeps auto_executable")

# Case 7: single entry → no conflict possible.
entries = [
    {"match_score": 3, "source": "ai-agent", "resolution_steps": ["fix"],
     "auto_executable": True, "success_count": 3, "failure_count": 0}
]
r = flag_runbook_conflicts(entries)
assert_eq(r[0].get("conflict"), None, "single entry never flagged")

# Case 8: cross-source conflict (ai-agent vs ops-mcp, tied score, different fix).
entries = [
    {"match_score": 2, "source": "ai-agent", "resolution_steps": ["restart-nginx"],
     "auto_executable": True, "success_count": 3, "failure_count": 0},
    {"match_score": 2, "source": "ops-mcp", "resolution": {"args": ["down"]},
     "auto_executable": True, "success_count": 3, "failure_count": 0},
]
r = flag_runbook_conflicts(entries)
assert_eq(r[0].get("conflict"), True, "cross-source disagreement flagged")
assert_eq(r[1].get("conflict"), True, "cross-source second entry also flagged")

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print(f"OK: 8 cases passed")
