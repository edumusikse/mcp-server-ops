#!/usr/bin/env python3
"""Self-audit drift detector.

Runs runbook_compliance.py and compares the most-recent N sessions against the
prior N sessions. Reports per-anti-pattern deltas and a REGRESS/IMPROVE/FLAT
verdict. Exits 1 if any anti-pattern count increased — suitable for a CI gate
or a daily cron.

Usage:
    python3 tests/self_audit.py [--window N]   (default N=5)
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMPLIANCE = REPO / "tests" / "runbook_compliance.py"

PATTERNS = ("runbook_missed", "runbook_late", "thrash")


def load_sessions() -> list:
    out = subprocess.run(
        ["python3", str(COMPLIANCE), "--pretty"],
        capture_output=True, text=True, check=False,
    )
    if out.returncode != 0:
        print(f"compliance harness exit={out.returncode}", file=sys.stderr)
        print(out.stderr, file=sys.stderr)
        sys.exit(2)
    return json.loads(out.stdout)["sessions"]


def count_patterns(sessions: list) -> dict:
    c = {p: 0 for p in PATTERNS}
    for s in sessions:
        for p in s.get("anti_patterns", []):
            c[p] = c.get(p, 0) + 1
    return c


def parse_window() -> int:
    if "--window" in sys.argv:
        return int(sys.argv[sys.argv.index("--window") + 1])
    return 5


def main() -> int:
    window = parse_window()
    sessions = load_sessions()

    if len(sessions) < window * 2:
        report = {
            "status": "insufficient_data",
            "sessions_available": len(sessions),
            "sessions_needed": window * 2,
            "all_sessions_pattern_counts": count_patterns(sessions),
        }
        print(json.dumps(report, indent=2))
        return 0

    recent = sessions[:window]
    prior = sessions[window:window * 2]
    r = count_patterns(recent)
    p = count_patterns(prior)
    deltas = {k: r[k] - p[k] for k in PATTERNS}
    regressed = [k for k, v in deltas.items() if v > 0]
    improved = [k for k, v in deltas.items() if v < 0]

    if regressed:
        verdict = "REGRESS"
    elif improved:
        verdict = "IMPROVE"
    else:
        verdict = "FLAT"

    report = {
        "window": window,
        "recent_sessions": [s["session_id"] for s in recent],
        "prior_sessions": [s["session_id"] for s in prior],
        "recent_counts": r,
        "prior_counts": p,
        "deltas": deltas,
        "regressed": regressed,
        "improved": improved,
        "verdict": verdict,
    }
    print(json.dumps(report, indent=2))
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main())
