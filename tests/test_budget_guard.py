#!/usr/bin/env python3
"""Test harness for the budget_guard hook.

Validates the pure-Python decision/tally/env/escape-hatch functions, and
smoke-tests the subprocess end-to-end with synthetic PreToolUse payloads to
verify exit codes, stderr, and the hookSpecificOutput JSON envelope.

Run: python3 tests/test_budget_guard.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO / ".claude" / "hooks" / "budget_guard.py"

spec = importlib.util.spec_from_file_location("budget_guard", HOOK_PATH)
bg = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bg)

failures: list[str] = []


def assert_eq(actual, expected, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def assert_in(needle: str, haystack: str, label: str) -> None:
    if needle not in haystack:
        failures.append(f"{label}: {needle!r} not found in {haystack[:200]!r}")


def write_transcript(events: list[dict]) -> str:
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for e in events:
        tf.write(json.dumps(e) + "\n")
    tf.close()
    return tf.name


NOW = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
NOW_TS = NOW.timestamp()


def ts_at(mins_ago: float) -> str:
    return (NOW - timedelta(minutes=mins_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def live_ts_at(mins_ago: float) -> str:
    """Real-time variant for subprocess tests — main() uses time.time() as now."""
    return datetime.fromtimestamp(_time.time() - mins_ago * 60, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )


def assistant(out_tokens, ts: str, **extra) -> dict:
    usage = {"output_tokens": out_tokens, **extra}
    return {"type": "assistant", "timestamp": ts, "message": {"usage": usage}}


# Kill switch may be set by the user while we're running. Tests that check
# cap behavior need to call decide() directly (pure function) or temporarily
# move the kill file aside for the subprocess cases.
_KILL_BACKUP = None


def suspend_kill_switch() -> None:
    """If the real kill switch file exists, rename it so subprocess tests see caps."""
    global _KILL_BACKUP
    if bg.KILL_SWITCH.exists():
        _KILL_BACKUP = bg.KILL_SWITCH.with_suffix(".testbackup")
        bg.KILL_SWITCH.rename(_KILL_BACKUP)


def restore_kill_switch() -> None:
    global _KILL_BACKUP
    if _KILL_BACKUP is not None and _KILL_BACKUP.exists():
        _KILL_BACKUP.rename(bg.KILL_SWITCH)
        _KILL_BACKUP = None


# ── Pure decide() / tally_transcript() ───────────────────────────────────────

# C1: under both caps → silent allow
t = bg.tally_transcript(write_transcript([assistant(1_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, time_cap_min=30, token_cap=100_000, kill=False, bypass=False)
assert_eq(r["decision"], "allow", "C1: under cap allow")
assert_eq(r["level"], "ok", "C1: ok level")

# C2: over token cap → hard deny
t = bg.tally_transcript(write_transcript([assistant(150_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False, False)
assert_eq(r["decision"], "deny", "C2: over token cap denied")
assert_eq(r["level"], "hard", "C2: hard level")
assert_in("BUDGET EXCEEDED", r["reason"], "C2: deny reason")
assert_in("150,000", r["reason"], "C2: actual count in reason")
assert_in("budget-off", r["reason"], "C2: deny reason mentions kill switch")

# C3: over time cap → hard deny
t = bg.tally_transcript(write_transcript([assistant(1_000, ts_at(45))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False, False)
assert_eq(r["decision"], "deny", "C3: over time cap denied")
assert_in("45.0 min", r["reason"], "C3: elapsed in reason")

# C4: warn at 50% of token cap, allow
t = bg.tally_transcript(write_transcript([assistant(60_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False, False)
assert_eq(r["decision"], "allow", "C4: warn still allows")
assert_eq(r["level"], "warn", "C4: 50% triggers warn")
assert_in("BUDGET WARN", r["reason"], "C4: warn reason")

# C5: warn at 50% of time cap, allow
t = bg.tally_transcript(write_transcript([assistant(1_000, ts_at(20))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False, False)
assert_eq(r["decision"], "allow", "C5: 50% time still allows")
assert_eq(r["level"], "warn", "C5: 50% time triggers warn")

# C6: bypass overrides hard deny
t = bg.tally_transcript(write_transcript([assistant(150_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False, True)
assert_eq(r["decision"], "allow", "C6: bypass overrides cap")
assert_eq(r["level"], "bypass", "C6: bypass level")

# C7: kill switch beats bypass beats cap (precedence)
r = bg.decide({"output_tokens": 999_999, "first_ts": ts_at(999)}, NOW_TS, 30, 100_000,
              kill=True, bypass=True)
assert_eq(r["level"], "kill", "C7: kill takes precedence over bypass")

# C8: missing transcript = zero tally, allow
t = bg.tally_transcript("/nonexistent/path-xyz.jsonl")
assert_eq(t["output_tokens"], 0, "C8: missing file zero tokens")
assert_eq(t["first_ts"], None, "C8: missing file no first_ts")
r = bg.decide(t, NOW_TS, 30, 100_000, False, False)
assert_eq(r["decision"], "allow", "C8: missing file allows")

# C9: cumulative across multiple turns
t = bg.tally_transcript(write_transcript([
    assistant(40_000, ts_at(10)),
    assistant(40_000, ts_at(8)),
    assistant(40_000, ts_at(5)),
]))
assert_eq(t["output_tokens"], 120_000, "C9: cumulative sum")

# C10: cache fields excluded from cap
t = bg.tally_transcript(write_transcript([
    {"type": "user", "timestamp": ts_at(20), "message": {"content": "hi"}},
    assistant(
        5_000, ts_at(15),
        input_tokens=100,
        cache_read_input_tokens=50_000,
        cache_creation_input_tokens=1_000,
    ),
]))
assert_eq(t["output_tokens"], 5_000, "C10: cache fields excluded from cap")

# C11: malformed JSON lines skipped, valid lines counted
tf = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
tf.write("not json\n")
tf.write(json.dumps(assistant(1_000, ts_at(5))) + "\n")
tf.write("\n")
tf.write("{broken\n")
tf.close()
t = bg.tally_transcript(tf.name)
assert_eq(t["output_tokens"], 1_000, "C11: malformed JSON lines skipped")

# C12: Bug #2 — non-numeric output_tokens skipped, others still counted
t = bg.tally_transcript(write_transcript([
    assistant("oops", ts_at(10)),
    assistant(2_500, ts_at(5)),
    assistant(None, ts_at(3)),
    assistant({"nested": 1}, ts_at(2)),
]))
assert_eq(t["output_tokens"], 2_500, "C12: non-numeric output_tokens skipped")

# C13: empty/missing usage on assistant message
t = bg.tally_transcript(write_transcript([
    {"type": "assistant", "timestamp": ts_at(5), "message": {}},
    assistant(2_000, ts_at(4)),
]))
assert_eq(t["output_tokens"], 2_000, "C13: missing usage tolerated")

# C14: parse_iso edge cases
assert_eq(bg.parse_iso(None), None, "C14a: None → None")
assert_eq(bg.parse_iso(""), None, "C14b: empty → None")
assert_eq(bg.parse_iso("garbage"), None, "C14c: garbage → None")
assert_eq(bg.parse_iso("2026-04-20T12:00:00.000Z"), NOW_TS, "C14d: Z suffix parsed")

# ── Bug #3 — positive_int_env validation ─────────────────────────────────────

orig_env = os.environ.copy()
try:
    os.environ.pop("BUDGET_X", None)
    assert_eq(bg.positive_int_env("BUDGET_X", 30), 30, "C15a: missing → default")
    os.environ["BUDGET_X"] = "60"
    assert_eq(bg.positive_int_env("BUDGET_X", 30), 60, "C15b: valid int → use it")
    os.environ["BUDGET_X"] = "0"
    assert_eq(bg.positive_int_env("BUDGET_X", 30), 30, "C15c: zero → fall back")
    os.environ["BUDGET_X"] = "-5"
    assert_eq(bg.positive_int_env("BUDGET_X", 30), 30, "C15d: negative → fall back")
    os.environ["BUDGET_X"] = "abc"
    assert_eq(bg.positive_int_env("BUDGET_X", 30), 30, "C15e: non-int → fall back")
    os.environ["BUDGET_X"] = ""
    assert_eq(bg.positive_int_env("BUDGET_X", 30), 30, "C15f: empty → fall back")
finally:
    os.environ.clear()
    os.environ.update(orig_env)

# ── Subprocess end-to-end ────────────────────────────────────────────────────
#
# The kill switch may be active (user set it to let us do this work). Move it
# aside temporarily so subprocess tests actually exercise the cap logic; we
# restore it at the end.

suspend_kill_switch()
try:

    def run_hook(payload: dict, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
        env = {**os.environ, **(env_overrides or {})}
        return subprocess.run(
            ["python3", str(HOOK_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True, timeout=10,
            env=env,
        )

    # C16: under cap → exit 0, no stderr, no stdout
    under_path = write_transcript([assistant(100, live_ts_at(1))])
    proc = run_hook({"transcript_path": under_path, "tool_name": "Read"})
    assert_eq(proc.returncode, 0, "C16: under cap exit 0")
    assert_eq(proc.stderr, "", "C16: no stderr under cap")
    assert_eq(proc.stdout, "", "C16: no stdout under cap (silent ok)")

    # C17: over cap → exit 2, stop directive in stderr
    over_path = write_transcript([assistant(200_000, live_ts_at(1))])
    proc = run_hook({"transcript_path": over_path, "tool_name": "Read"})
    assert_eq(proc.returncode, 2, "C17: over cap exit 2")
    assert_in("BUDGET EXCEEDED", proc.stderr, "C17: stderr contains stop directive")

    # C18: env override raises cap, deny becomes allow
    proc = run_hook({"transcript_path": over_path, "tool_name": "Read"},
                    env_overrides={"BUDGET_TOKEN_OUTPUT": "500000", "BUDGET_TIME_MIN": "60"})
    assert_eq(proc.returncode, 0, "C18: env override lifts deny")

    # C19: Bug #3 — BUDGET_TOKEN_OUTPUT=0 falls back to default, no insta-deny
    small_path = write_transcript([assistant(100, live_ts_at(1))])
    proc = run_hook({"transcript_path": small_path, "tool_name": "Read"},
                    env_overrides={"BUDGET_TOKEN_OUTPUT": "0"})
    assert_eq(proc.returncode, 0, "C19: zero cap falls back to default → allow")

    # C20: BUDGET_TIME_MIN=0 falls back to default
    proc = run_hook({"transcript_path": small_path, "tool_name": "Read"},
                    env_overrides={"BUDGET_TIME_MIN": "0"})
    assert_eq(proc.returncode, 0, "C20: zero time cap falls back to default → allow")

    # C21: missing transcript_path → exit 0, no-op
    proc = run_hook({"tool_name": "Read"})
    assert_eq(proc.returncode, 0, "C21: missing transcript_path → no-op allow")

    # C22: malformed stdin payload → exit 0, no-op
    proc = subprocess.run(
        ["python3", str(HOOK_PATH)],
        input="not json at all",
        capture_output=True, text=True, timeout=10,
    )
    assert_eq(proc.returncode, 0, "C22: malformed payload → no-op allow")

    # C23: Bug #1 — warn emits hookSpecificOutput envelope
    warn_path = write_transcript([assistant(60_000, live_ts_at(5))])
    proc = run_hook({"transcript_path": warn_path, "tool_name": "Read"})
    assert_eq(proc.returncode, 0, "C23: warn exit 0")
    out = json.loads(proc.stdout)
    assert_eq("hookSpecificOutput" in out, True, "C23: stdout has hookSpecificOutput key")
    hso = out["hookSpecificOutput"]
    assert_eq(hso.get("hookEventName"), "PreToolUse", "C23: hookEventName == PreToolUse")
    assert_in("BUDGET WARN", hso.get("additionalContext", ""),
              "C23: warn message in hookSpecificOutput.additionalContext")
    assert_eq("additionalContext" not in out, True,
              "C23: no top-level additionalContext (UserPromptSubmit-only field)")

    # C24: Bug #4 — bypass emits visible hookSpecificOutput
    real_bypass = "/tmp/claude-hook-bypass"
    pre_existing_bypass = os.path.exists(real_bypass)
    if not pre_existing_bypass:
        with open(real_bypass, "w") as f:
            f.write("CONFIRMED\n")
        try:
            proc = run_hook({"transcript_path": over_path, "tool_name": "Read"})
            assert_eq(proc.returncode, 0, "C24: bypass allows over-cap")
            out = json.loads(proc.stdout)
            assert_in("BYPASS active", out.get("hookSpecificOutput", {}).get("additionalContext", ""),
                      "C24: bypass status visible in hookSpecificOutput")
        finally:
            os.unlink(real_bypass)

    # C25: bypass file with trailing comment (the lockout fix)
    if not os.path.exists(real_bypass):
        with open(real_bypass, "w") as f:
            f.write("CONFIRMED     # 5-min unblock\n")
        try:
            proc = run_hook({"transcript_path": over_path, "tool_name": "Read"})
            assert_eq(proc.returncode, 0, "C25: bypass with trailing comment still works")
        finally:
            os.unlink(real_bypass)

    # C26: stale bypass file rejected (mtime > 300s)
    if not os.path.exists(real_bypass):
        with open(real_bypass, "w") as f:
            f.write("CONFIRMED\n")
        try:
            old_ts = _time.time() - 400
            os.utime(real_bypass, (old_ts, old_ts))
            assert_eq(bg.bypass_active(), False, "C26: stale bypass file rejected")
        finally:
            os.unlink(real_bypass)

    # C27: kill switch unit — kill_switch_active True when file present
    kill_path = bg.KILL_SWITCH
    kill_path.parent.mkdir(parents=True, exist_ok=True)
    kill_path.touch()
    try:
        assert_eq(bg.kill_switch_active(), True, "C27a: kill file present → True")
        proc = run_hook({"transcript_path": over_path, "tool_name": "Read"})
        assert_eq(proc.returncode, 0, "C27b: kill switch overrides over-cap")
        out = json.loads(proc.stdout) if proc.stdout else {}
        assert_in("KILL SWITCH", out.get("hookSpecificOutput", {}).get("additionalContext", ""),
                  "C27c: kill status visible in hookSpecificOutput")
    finally:
        if kill_path.exists():
            kill_path.unlink()

    # C28: kill switch unit — False when file absent
    assert_eq(bg.kill_switch_active(), False, "C28: no file → kill_switch_active False")

finally:
    restore_kill_switch()


if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 28 cases passed")
