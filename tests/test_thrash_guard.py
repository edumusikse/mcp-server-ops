#!/usr/bin/env python3
"""Unit test for the anti-thrash guard.

Tests the pure-Python guard logic without booting the MCP server.
Run: `python3 tests/test_thrash_guard.py`
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from guards import thrash_guard, reset_thrash_window  # noqa: E402

failures: list[str] = []


def assert_eq(actual, expected, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


# Case 1: 4 identical calls — no stop yet.
reset_thrash_window()
for _ in range(4):
    stop = thrash_guard("wp_cli", "ksm-wp")
assert_eq(stop, None, "4 identical calls do not trip")

# Case 2: 5th identical call trips.
reset_thrash_window()
stop = None
for _ in range(5):
    stop = thrash_guard("wp_cli", "ksm-wp")
assert_eq(stop is not None, True, "5th identical call trips")
assert_eq(stop["error"], "thrash_stop", "error code is thrash_stop")
assert_eq(stop["consecutive_calls"], 5, "consecutive_calls = 5")

# Case 3: different target resets the run.
reset_thrash_window()
for _ in range(4):
    thrash_guard("wp_cli", "ksm-wp")
stop = thrash_guard("wp_cli", "frid-wp")
assert_eq(stop, None, "different target resets")
for _ in range(3):
    thrash_guard("wp_cli", "frid-wp")
stop = thrash_guard("wp_cli", "frid-wp")
assert_eq(stop is not None, True, "5 on new target trips")

# Case 4: different tool resets the run.
reset_thrash_window()
for _ in range(4):
    thrash_guard("wp_cli", "ksm-wp")
thrash_guard("tail_logs", "ksm-wp")
stop = thrash_guard("wp_cli", "ksm-wp")
assert_eq(stop, None, "different tool resets")

# Case 5: alternating calls never trigger.
reset_thrash_window()
stop = None
for _ in range(10):
    thrash_guard("wp_cli", "ksm-wp")
    s = thrash_guard("read_file", "/var/log/x")
    if s:
        stop = s
assert_eq(stop, None, "alternating calls never trip")

# Case 6: None target treated as empty string, still trips at 5.
reset_thrash_window()
stop = None
for _ in range(5):
    stop = thrash_guard("list_containers", None)
assert_eq(stop is not None, True, "None target still trips at 5")

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 6 cases passed")
