#!/usr/bin/env python3
"""Test harness for the budget_guard hook.

Validates the pure-Python decision and tally functions without invoking the
hook subprocess. Also smoke-tests the subprocess end-to-end with a synthetic
PreToolUse payload to verify exit codes and stderr.

Run: python3 tests/test_budget_guard.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
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
        failures.append(f"{label}: {needle!r} not found in {haystack!r}")


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


def assistant(out_tokens: int, ts: str, **extra) -> dict:
    usage = {"output_tokens": out_tokens, **extra}
    return {"type": "assistant", "timestamp": ts, "message": {"usage": usage}}


# ── Case 1: under both caps → silent allow ───────────────────────────────────
t = bg.tally_transcript(write_transcript([assistant(1_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, time_cap_min=30, token_cap=100_000, bypass=False)
assert_eq(r["decision"], "allow", "C1: under cap allow")
assert_eq(r["level"], "ok", "C1: ok level")

# ── Case 2: over token cap → hard deny ───────────────────────────────────────
t = bg.tally_transcript(write_transcript([assistant(150_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False)
assert_eq(r["decision"], "deny", "C2: over token cap denied")
assert_eq(r["level"], "hard", "C2: hard level")
assert_in("BUDGET EXCEEDED", r["reason"], "C2: deny reason")
assert_in("150,000", r["reason"], "C2: actual count in reason")

# ── Case 3: over time cap → hard deny ────────────────────────────────────────
t = bg.tally_transcript(write_transcript([assistant(1_000, ts_at(45))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False)
assert_eq(r["decision"], "deny", "C3: over time cap denied")
assert_in("45.0 min", r["reason"], "C3: elapsed in reason")

# ── Case 4: warn at 50% of token cap, allow ──────────────────────────────────
t = bg.tally_transcript(write_transcript([assistant(60_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False)
assert_eq(r["decision"], "allow", "C4: warn still allows")
assert_eq(r["level"], "warn", "C4: 50% triggers warn")
assert_in("BUDGET WARN", r["reason"], "C4: warn reason")

# ── Case 5: warn at 50% of time cap, allow ───────────────────────────────────
t = bg.tally_transcript(write_transcript([assistant(1_000, ts_at(20))]))
r = bg.decide(t, NOW_TS, 30, 100_000, False)
assert_eq(r["decision"], "allow", "C5: 50% time still allows")
assert_eq(r["level"], "warn", "C5: 50% time triggers warn")

# ── Case 6: bypass overrides hard deny ───────────────────────────────────────
t = bg.tally_transcript(write_transcript([assistant(150_000, ts_at(5))]))
r = bg.decide(t, NOW_TS, 30, 100_000, bypass=True)
assert_eq(r["decision"], "allow", "C6: bypass overrides")
assert_eq(r["level"], "bypass", "C6: bypass level")

# ── Case 7: missing transcript = zero tally, allow ───────────────────────────
t = bg.tally_transcript("/nonexistent/path-xyz.jsonl")
assert_eq(t["output_tokens"], 0, "C7: missing file zero tokens")
assert_eq(t["first_ts"], None, "C7: missing file no first_ts")
r = bg.decide(t, NOW_TS, 30, 100_000, False)
assert_eq(r["decision"], "allow", "C7: missing file allows")

# ── Case 8: cumulative across multiple turns ─────────────────────────────────
t = bg.tally_transcript(write_transcript([
    assistant(40_000, ts_at(10)),
    assistant(40_000, ts_at(8)),
    assistant(40_000, ts_at(5)),
]))
assert_eq(t["output_tokens"], 120_000, "C8: cumulative sum")
r = bg.decide(t, NOW_TS, 30, 100_000, False)
assert_eq(r["decision"], "deny", "C8: cumulative trips cap")

# ── Case 9: real schema with cache fields — only output_tokens counted ───────
t = bg.tally_transcript(write_transcript([
    {"type": "user", "timestamp": ts_at(20), "message": {"content": "hi"}},
    assistant(
        5_000, ts_at(15),
        input_tokens=100,
        cache_read_input_tokens=50_000,
        cache_creation_input_tokens=1_000,
    ),
]))
assert_eq(t["output_tokens"], 5_000, "C9: cache fields excluded from cap")

# ── Case 10: malformed JSON lines skipped, valid lines still counted ─────────
tf = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
tf.write("not json\n")
tf.write(json.dumps(assistant(1_000, ts_at(5))) + "\n")
tf.write("\n")  # blank
tf.write("{broken\n")
tf.close()
t = bg.tally_transcript(tf.name)
assert_eq(t["output_tokens"], 1_000, "C10: malformed lines skipped, valid counted")

# ── Case 11: empty/missing usage on assistant message → zero contribution ────
t = bg.tally_transcript(write_transcript([
    {"type": "assistant", "timestamp": ts_at(5), "message": {}},
    assistant(2_000, ts_at(4)),
]))
assert_eq(t["output_tokens"], 2_000, "C11: missing usage tolerated")

# ── Case 12: parse_iso handles Z suffix and bad input ────────────────────────
assert_eq(bg.parse_iso(None), None, "C12a: None → None")
assert_eq(bg.parse_iso(""), None, "C12b: empty → None")
assert_eq(bg.parse_iso("garbage"), None, "C12c: garbage → None")
v = bg.parse_iso("2026-04-20T12:00:00.000Z")
assert_eq(v == NOW_TS, True, "C12d: Z suffix parsed")

# ── Case 13: subprocess end-to-end — under cap → exit 0, no stderr ───────────
under_path = write_transcript([assistant(100, ts_at(1))])
proc = subprocess.run(
    ["python3", str(HOOK_PATH)],
    input=json.dumps({"transcript_path": under_path, "tool_name": "Read"}),
    capture_output=True, text=True, timeout=10,
)
assert_eq(proc.returncode, 0, "C13: under cap exit 0")
assert_eq(proc.stderr, "", "C13: no stderr under cap")

# ── Case 14: subprocess end-to-end — over cap → exit 2 with stderr ───────────
over_path = write_transcript([assistant(200_000, ts_at(1))])
proc = subprocess.run(
    ["python3", str(HOOK_PATH)],
    input=json.dumps({"transcript_path": over_path, "tool_name": "Read"}),
    capture_output=True, text=True, timeout=10,
)
assert_eq(proc.returncode, 2, "C14: over cap exit 2")
assert_in("BUDGET EXCEEDED", proc.stderr, "C14: stderr contains stop directive")

# ── Case 15: subprocess — env override raises cap, deny becomes allow ────────
proc = subprocess.run(
    ["python3", str(HOOK_PATH)],
    input=json.dumps({"transcript_path": over_path, "tool_name": "Read"}),
    capture_output=True, text=True, timeout=10,
    env={**os.environ, "BUDGET_TOKEN_OUTPUT": "500000", "BUDGET_TIME_MIN": "60"},
)
assert_eq(proc.returncode, 0, "C15: env override lifts deny")

# ── Case 16: subprocess — missing transcript_path → exit 0, no-op ────────────
proc = subprocess.run(
    ["python3", str(HOOK_PATH)],
    input=json.dumps({"tool_name": "Read"}),
    capture_output=True, text=True, timeout=10,
)
assert_eq(proc.returncode, 0, "C16: missing transcript_path → no-op allow")

# ── Case 17: subprocess — malformed stdin payload → exit 0, no-op ────────────
proc = subprocess.run(
    ["python3", str(HOOK_PATH)],
    input="not json at all",
    capture_output=True, text=True, timeout=10,
)
assert_eq(proc.returncode, 0, "C17: malformed payload → no-op allow")

# ── Case 18: subprocess warn — exit 0 with additionalContext on stdout ───────
warn_path = write_transcript([assistant(60_000, ts_at(5))])
proc = subprocess.run(
    ["python3", str(HOOK_PATH)],
    input=json.dumps({"transcript_path": warn_path, "tool_name": "Read"}),
    capture_output=True, text=True, timeout=10,
)
assert_eq(proc.returncode, 0, "C18: warn exit 0")
try:
    out = json.loads(proc.stdout)
    assert_in("BUDGET WARN", out.get("additionalContext", ""), "C18: warn in additionalContext")
except (json.JSONDecodeError, ValueError):
    failures.append(f"C18: warn stdout not JSON: {proc.stdout!r}")


if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 18 cases passed")
