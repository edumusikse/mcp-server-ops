#!/usr/bin/env python3
"""Synthetic tests for runbook_compliance.py.

These tests prove the transcript analyzer catches the behaviors it is supposed
to enforce: missed runbook lookup, late lookup, and repeated-tool thrash.

Run: python3 tests/test_runbook_compliance.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOD_PATH = REPO / "tests" / "runbook_compliance.py"

spec = importlib.util.spec_from_file_location("runbook_compliance_mod", MOD_PATH)
rc = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = rc
spec.loader.exec_module(rc)

failures: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        failures.append(label)


def tool(name: str, input_: dict | None = None) -> dict:
    return {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": name, "input": input_ or {}}
            ]
        },
    }


def transcript(events: list[dict]) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for event in events:
        f.write(json.dumps(event) + "\n")
    f.close()
    return Path(f.name)


def analyze(events: list[dict]):
    return rc.analyze(transcript(events))


base_user = {"type": "user", "message": {"content": "fix ops issue"}}

# C1: no operational triage trigger means the analyzer stays quiet.
r = analyze([base_user, tool("Read", {"file_path": "README.md"})])
check(r.anti_patterns == [], "C1 local non-ops session passes")

# C2: lookup_runbook before operational ops tools passes.
r = analyze([
    base_user,
    tool("mcp__ops__lookup_runbook", {"problem_description": "mail failures"}),
    tool("mcp__ops__fleet_status"),
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
])
check(r.anti_patterns == [], "C2 runbook-first ops session passes")

# C3: triage with no lookup is a miss.
r = analyze([
    base_user,
    tool("mcp__ops__fleet_status"),
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
])
check("runbook_missed" in r.anti_patterns, "C3 missed runbook detected")

# C4: any operational ops tool before lookup is late.
r = analyze([
    base_user,
    tool("mcp__ops__fleet_status"),
    tool("mcp__ops__lookup_runbook", {"problem_description": "late lookup"}),
])
check("runbook_late" in r.anti_patterns, "C4 late runbook detected")

# C5: five identical MCP tool+target calls in a row is thrash.
r = analyze([
    base_user,
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
    tool("mcp__ops__tail_logs", {"container": "ksm-wp"}),
])
check("thrash" in r.anti_patterns, "C5 thrash detected")

# C6: context/runbook meta tools are exempt before lookup.
r = analyze([
    base_user,
    tool("mcp__ops__read_doc", {"name": "ops-map"}),
    tool("mcp__ops__ai_cost_summary"),
])
check(r.anti_patterns == [], "C6 exempt ops meta tools pass")

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 6 cases passed")
