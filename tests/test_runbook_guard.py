#!/usr/bin/env python3
"""Tests for .claude/hooks/runbook_guard.py.

Coverage:
    - decide() precedence: kill > bypass > non-ops > exempt > runbook-present > block
    - operational mcp__ops__ tool before lookup_runbook → block (exit 2)
    - exempt ops tools (read_doc, record_runbook_outcome, ai_cost_summary) allow
      even without prior lookup_runbook
    - lookup_runbook already in transcript → allow
    - non-ops tool names → allow (hook is matcher-scoped but stays defensive)
    - exempt set must match tests/runbook_compliance.py RUNBOOK_EXEMPT_TOOLS
    - bypass constants must match block-ssh.py / budget_guard.py
    - first-token CONFIRMED bypass parsing
    - malformed stdin → exit 0 (fail-open)
    - kill switch → exit 0 with context envelope
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "runbook_guard.py"
BYPASS_FILE = "/tmp/claude-hook-bypass"

spec = importlib.util.spec_from_file_location("runbook_guard_mod", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

compliance_spec = importlib.util.spec_from_file_location(
    "runbook_compliance_mod", REPO / "tests" / "runbook_compliance.py"
)
compliance = importlib.util.module_from_spec(compliance_spec)
sys.modules[compliance_spec.name] = compliance
compliance_spec.loader.exec_module(compliance)

block_ssh_spec = importlib.util.spec_from_file_location(
    "block_ssh_mod", REPO / ".claude" / "hooks" / "block-ssh.py"
)
block_ssh = importlib.util.module_from_spec(block_ssh_spec)
block_ssh_spec.loader.exec_module(block_ssh)

budget_spec = importlib.util.spec_from_file_location(
    "budget_guard_mod", REPO / ".claude" / "hooks" / "budget_guard.py"
)
budget = importlib.util.module_from_spec(budget_spec)
budget_spec.loader.exec_module(budget)

failures: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        failures.append(label)


def write_transcript(events: list[dict]) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for ev in events:
        f.write(json.dumps(ev) + "\n")
    f.close()
    return Path(f.name)


def tool_event(name: str, input_: dict | None = None) -> dict:
    return {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": name, "input": input_ or {}}
            ]
        },
    }


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )


def suspend_kill_switch() -> Path | None:
    ks = guard.KILL_SWITCH
    if ks.exists():
        stash = ks.with_suffix(".stash")
        ks.rename(stash)
        return stash
    return None


def restore_kill_switch(stash: Path | None) -> None:
    if stash and stash.exists():
        stash.rename(guard.KILL_SWITCH)


def clear_bypass() -> None:
    try:
        os.unlink(BYPASS_FILE)
    except FileNotFoundError:
        pass


# ─── Cross-hook constant alignment ─────────────────────────────────────────

check(
    guard.RUNBOOK_EXEMPT_TOOLS == set(compliance.RUNBOOK_EXEMPT_TOOLS),
    "A1 runbook_guard exempt set matches runbook_compliance.py",
)
check(guard.RUNBOOK_TOOL == compliance.RUNBOOK_TOOL, "A2 RUNBOOK_TOOL aligned")
check(
    guard.BYPASS_FILE == block_ssh.BYPASS_FILE == budget.BYPASS_FILE,
    "A3 bypass file path aligned across all three hooks",
)
check(
    guard.BYPASS_TTL_SEC == block_ssh.BYPASS_TTL_SEC == budget.BYPASS_TTL_SEC == 300,
    "A4 bypass TTL aligned (300s)",
)
check(
    guard.BYPASS_TOKEN == block_ssh.BYPASS_TOKEN == budget.BYPASS_TOKEN == "CONFIRMED",
    "A5 bypass token aligned (CONFIRMED)",
)
check(
    guard.KILL_SWITCH != block_ssh.KILL_SWITCH and guard.KILL_SWITCH != budget.KILL_SWITCH,
    "A6 kill switch paths distinct from other hooks",
)

# ─── Pure decide() cases ───────────────────────────────────────────────────

# Transcript with no lookup
no_lookup = write_transcript([tool_event("mcp__ops__fleet_status")])
# Transcript where lookup already ran
with_lookup = write_transcript([
    tool_event("mcp__ops__lookup_runbook", {"problem_description": "mail failures"}),
])

# C1: operational call without lookup blocks
r = guard.decide("mcp__ops__tail_logs", str(no_lookup), kill=False, bypass=False)
check(r["decision"] == "block" and r["level"] == "hard", "C1 operational without lookup blocks")

# C2: operational call with lookup in transcript allows
r = guard.decide("mcp__ops__tail_logs", str(with_lookup), kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "runbook-ok", "C2 runbook-present allows")

# C3: lookup_runbook itself always allowed (exempt)
r = guard.decide("mcp__ops__lookup_runbook", str(no_lookup), kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "exempt", "C3 lookup_runbook exempt")

# C4: read_doc exempt
r = guard.decide("mcp__ops__read_doc", str(no_lookup), kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "exempt", "C4 read_doc exempt")

# C5: record_runbook_outcome exempt
r = guard.decide("mcp__ops__record_runbook_outcome", str(no_lookup), kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "exempt", "C5 record_runbook_outcome exempt")

# C6: ai_cost_summary exempt
r = guard.decide("mcp__ops__ai_cost_summary", str(no_lookup), kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "exempt", "C6 ai_cost_summary exempt")

# C7: non-ops tool name allows (hook is matcher-scoped but stays defensive)
r = guard.decide("Read", str(no_lookup), kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "non-ops", "C7 non-ops tool allowed")

# C8: bypass overrides block
r = guard.decide("mcp__ops__tail_logs", str(no_lookup), kill=False, bypass=True)
check(r["decision"] == "allow" and r["level"] == "bypass", "C8 bypass overrides block")

# C9: kill switch overrides everything
r = guard.decide("mcp__ops__tail_logs", str(no_lookup), kill=True, bypass=False)
check(r["decision"] == "allow" and r["level"] == "kill", "C9 kill overrides block")

# C10: kill precedence over bypass
r = guard.decide("mcp__ops__tail_logs", str(no_lookup), kill=True, bypass=True)
check(r["decision"] == "allow" and r["level"] == "kill", "C10 kill > bypass precedence")

# C11: missing transcript path → block (can't prove lookup happened)
r = guard.decide("mcp__ops__tail_logs", "", kill=False, bypass=False)
check(r["decision"] == "block", "C11 missing transcript path blocks operational")

# C12: missing transcript file → block (same reason)
r = guard.decide("mcp__ops__tail_logs", "/no/such/file.jsonl", kill=False, bypass=False)
check(r["decision"] == "block", "C12 missing transcript file blocks operational")

# ─── Transcript scanner edge cases ────────────────────────────────────────

# C13: malformed lines in transcript are skipped, valid lookup still found
mixed = Path(tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name)
mixed.write_text(
    "not json\n"
    + json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n"
    + json.dumps(tool_event("mcp__ops__lookup_runbook", {"problem_description": "x"})) + "\n"
)
check(guard.transcript_has_runbook(str(mixed)) is True, "C13 malformed lines skipped, lookup still found")

# C14: user messages mentioning lookup_runbook do NOT count (only assistant tool_use)
user_only = write_transcript([
    {"type": "user", "message": {"content": "please call mcp__ops__lookup_runbook"}},
])
check(guard.transcript_has_runbook(str(user_only)) is False, "C14 user text does not satisfy lookup")

# ─── Bypass file parsing ───────────────────────────────────────────────────

clear_bypass()
check(guard.bypass_active() is False, "C15 no bypass file → inactive")

with open(BYPASS_FILE, "w") as f:
    f.write("CONFIRMED")
check(guard.bypass_active() is True, "C16 CONFIRMED exact")

with open(BYPASS_FILE, "w") as f:
    f.write("CONFIRMED # 5-min unblock")
check(guard.bypass_active() is True, "C17 CONFIRMED with comment (first-token)")

with open(BYPASS_FILE, "w") as f:
    f.write("CONFIRMED")
old_ts = time.time() - (guard.BYPASS_TTL_SEC + 60)
os.utime(BYPASS_FILE, (old_ts, old_ts))
check(guard.bypass_active() is False, "C18 expired bypass rejected")

with open(BYPASS_FILE, "w") as f:
    f.write("YES")
check(guard.bypass_active() is False, "C19 wrong token rejected")

clear_bypass()

# ─── Subprocess end-to-end ────────────────────────────────────────────────

stash = suspend_kill_switch()
try:
    # C20: blocked → exit 2 with instructional stderr
    clear_bypass()
    p = run_hook({
        "tool_name": "mcp__ops__tail_logs",
        "transcript_path": str(no_lookup),
    })
    check(p.returncode == 2, "C20 missing-runbook exits 2")
    check("RUNBOOK-FIRST" in p.stderr, "C20 block reason in stderr")
    check("lookup_runbook" in p.stderr, "C20 block instructs to call lookup_runbook")

    # C21: runbook present → exit 0
    p = run_hook({
        "tool_name": "mcp__ops__tail_logs",
        "transcript_path": str(with_lookup),
    })
    check(p.returncode == 0, "C21 runbook-present exits 0")

    # C22: exempt tool → exit 0 even without lookup
    p = run_hook({
        "tool_name": "mcp__ops__read_doc",
        "transcript_path": str(no_lookup),
    })
    check(p.returncode == 0, "C22 exempt tool exits 0")

    # C23: non-ops tool name → exit 0
    p = run_hook({
        "tool_name": "Read",
        "transcript_path": str(no_lookup),
    })
    check(p.returncode == 0, "C23 non-ops tool exits 0")

    # C24: bypass active → block lifted with context
    with open(BYPASS_FILE, "w") as f:
        f.write("CONFIRMED")
    p = run_hook({
        "tool_name": "mcp__ops__tail_logs",
        "transcript_path": str(no_lookup),
    })
    check(p.returncode == 0, "C24 bypass lifts block")
    check("RUNBOOK-GUARD BYPASS active" in p.stdout, "C24 bypass context emitted")
    clear_bypass()

    # C25: malformed JSON → fail-open
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        timeout=10,
    )
    check(r.returncode == 0, "C25 malformed stdin exits 0 (fail-open)")

    # C26: missing tool_name → fail-open (treated as non-ops)
    p = run_hook({"transcript_path": str(no_lookup)})
    check(p.returncode == 0, "C26 missing tool_name fails open")

    # C27: missing transcript_path for operational tool → block (can't prove lookup)
    p = run_hook({"tool_name": "mcp__ops__tail_logs"})
    check(p.returncode == 2, "C27 missing transcript_path blocks operational")
finally:
    restore_kill_switch(stash)

# C28: kill switch → allow + kill-context
ks = guard.KILL_SWITCH
ks.parent.mkdir(parents=True, exist_ok=True)
ks_stash = suspend_kill_switch()
try:
    ks.touch()
    p = run_hook({
        "tool_name": "mcp__ops__tail_logs",
        "transcript_path": str(no_lookup),
    })
    check(p.returncode == 0, "C28 kill switch lifts block")
    check("KILL SWITCH" in p.stdout, "C28 kill context emitted")
finally:
    if ks.exists():
        ks.unlink()
    restore_kill_switch(ks_stash)

# Clean up temp transcripts
for p in (no_lookup, with_lookup, mixed, user_only):
    try:
        os.unlink(p)
    except FileNotFoundError:
        pass

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 38 cases passed")
