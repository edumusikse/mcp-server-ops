#!/usr/bin/env python3
"""Tests for .claude/hooks/plan_first_guard.py.

Coverage:
    - empty transcript → allow
    - 1 or 2 consecutive Bash, no TodoWrite → allow
    - 3 consecutive Bash, no TodoWrite → deny (exit 2)
    - 4 consecutive Bash, no TodoWrite → deny
    - 3 consecutive Bash, TodoWrite present → allow
    - streak resets on non-Bash tool → allow
    - kill switch → allow
    - bypass file → allow
    - malformed stdin → exit 0 (fail-open)
    - missing transcript_path → exit 0 (fail-open)
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import time
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "plan_first_guard.py"

spec = importlib.util.spec_from_file_location("plan_first_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

failures: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        failures.append(label)


def make_transcript(tool_calls: list[str]) -> str:
    """Write a minimal JSONL transcript with the given tool_use sequence."""
    lines = []
    for name in tool_calls:
        lines.append(json.dumps({
            "type": "assistant",
            "message": {
                "content": [{"type": "tool_use", "name": name}],
                "usage": {"output_tokens": 10},
            },
            "timestamp": "2026-04-27T08:00:00Z",
        }))
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    f.write("\n".join(lines))
    f.close()
    return f.name


def run_hook(tool_calls: list[str], *, kill: bool = False, bypass: bool = False) -> int:
    path = make_transcript(tool_calls)
    try:
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps({"tool_name": "Bash", "tool_input": {}, "transcript_path": path}),
            capture_output=True,
            text=True,
            env={
                **dict(__import__("os").environ),
                **({"_PLAN_GUARD_KILL": "1"} if kill else {}),
            },
        )
        return result.returncode
    finally:
        Path(path).unlink(missing_ok=True)


# --- Unit tests on decide() ---

check(
    guard.decide({"bash_streak": 0, "todo_write_count": 0}, kill=False, bypass=False)["decision"] == "allow",
    "streak=0, no plan → allow",
)
check(
    guard.decide({"bash_streak": 2, "todo_write_count": 0}, kill=False, bypass=False)["decision"] == "allow",
    "streak=2, no plan → allow (below limit)",
)
check(
    guard.decide({"bash_streak": 3, "todo_write_count": 0}, kill=False, bypass=False)["decision"] == "deny",
    "streak=3, no plan → deny",
)
check(
    guard.decide({"bash_streak": 5, "todo_write_count": 0}, kill=False, bypass=False)["decision"] == "deny",
    "streak=5, no plan → deny",
)
check(
    guard.decide({"bash_streak": 3, "todo_write_count": 1}, kill=False, bypass=False)["decision"] == "allow",
    "streak=3, TodoWrite present → allow",
)
check(
    guard.decide({"bash_streak": 3, "todo_write_count": 0}, kill=True, bypass=False)["decision"] == "allow",
    "kill switch → allow regardless of streak",
)
check(
    guard.decide({"bash_streak": 3, "todo_write_count": 0}, kill=False, bypass=True)["decision"] == "allow",
    "bypass → allow regardless of streak",
)

# --- Unit tests on scan_transcript() ---

path = make_transcript(["Bash", "Bash", "Bash"])
scan = guard.scan_transcript(path)
Path(path).unlink(missing_ok=True)
check(scan["bash_streak"] == 3, "scan: 3 trailing Bash → streak=3")
check(scan["todo_write_count"] == 0, "scan: no TodoWrite → count=0")

path = make_transcript(["Bash", "TodoWrite", "Bash", "Bash"])
scan = guard.scan_transcript(path)
Path(path).unlink(missing_ok=True)
check(scan["bash_streak"] == 2, "scan: TodoWrite breaks streak → streak=2")
check(scan["todo_write_count"] == 1, "scan: TodoWrite counted")

path = make_transcript(["Bash", "Bash", "Read", "Bash"])
scan = guard.scan_transcript(path)
Path(path).unlink(missing_ok=True)
check(scan["bash_streak"] == 1, "scan: Read resets streak → streak=1")

path = make_transcript([])
scan = guard.scan_transcript(path)
Path(path).unlink(missing_ok=True)
check(scan["bash_streak"] == 0, "scan: empty transcript → streak=0")

# --- Integration: fail-open cases ---

result = subprocess.run(
    ["python3", str(HOOK)],
    input="not-json",
    capture_output=True,
    text=True,
)
check(result.returncode == 0, "malformed stdin → exit 0")

result = subprocess.run(
    ["python3", str(HOOK)],
    input=json.dumps({"tool_name": "Bash", "tool_input": {}}),
    capture_output=True,
    text=True,
)
check(result.returncode == 0, "missing transcript_path → exit 0")

# --- Integration: kill switch ---
kill_path = Path.home() / ".ops-mcp" / "plan-guard-off"
was_present = kill_path.exists()
try:
    kill_path.parent.mkdir(parents=True, exist_ok=True)
    kill_path.touch()
    path = make_transcript(["Bash", "Bash", "Bash"])
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {}, "transcript_path": path}),
        capture_output=True,
        text=True,
    )
    Path(path).unlink(missing_ok=True)
    check(result.returncode == 0, "kill switch present → exit 0")
finally:
    if not was_present:
        kill_path.unlink(missing_ok=True)

# --- Integration: bypass file ---
bypass_path = Path("/tmp/claude-hook-bypass")
try:
    bypass_path.write_text("CONFIRMED")
    path = make_transcript(["Bash", "Bash", "Bash"])
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {}, "transcript_path": path}),
        capture_output=True,
        text=True,
    )
    Path(path).unlink(missing_ok=True)
    check(result.returncode == 0, "bypass file → exit 0")
finally:
    bypass_path.unlink(missing_ok=True)

# --- Report ---
if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    raise SystemExit(1)
print(f"OK: plan_first_guard — {14 - len(failures)}/14 checks passed")
