#!/usr/bin/env python3
"""Unit tests for the payload-similarity guard."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from guards import (  # noqa: E402
    payload_similarity_guard,
    reset_payload_window,
    PAYLOAD_MIN_BYTES,
    PAYLOAD_SIM_LIMIT,
)

failures: list[str] = []


def assert_eq(actual, expected, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


BIG = "A" * (PAYLOAD_MIN_BYTES + 100)
BIG_ALT = "B" * (PAYLOAD_MIN_BYTES + 100)
SMALL = "A" * 1024

# Case 1: small payload — never tracked or tripped.
reset_payload_window()
for tool in ("read_file", "write_file", "extra1", "extra2"):
    stop = payload_similarity_guard(tool, SMALL)
assert_eq(stop, None, "small payloads never trip")

# Case 2: same big blob through PAYLOAD_SIM_LIMIT distinct tools → trip.
# The real MCP shuttle is read_file → write_file (the two tools that move
# significant content). PAYLOAD_SIM_LIMIT=2 catches exactly that.
reset_payload_window()
payload_similarity_guard("read_file", BIG)
stop = payload_similarity_guard("write_file", BIG)
assert_eq(stop is not None, True, "read_file → write_file with same blob → trip")
assert_eq(stop["error"], "payload_thrash_stop", "error code is payload_thrash_stop")
assert_eq(sorted(stop["distinct_tools"]), ["read_file", "write_file"],
          "distinct_tools is the read+write pair")

# Case 3: same tool repeatedly with same blob → does NOT trip payload guard
# (that's thrash_guard's job, not this guard's job).
reset_payload_window()
stop = None
for _ in range(5):
    stop = payload_similarity_guard("write_file", BIG)
assert_eq(stop, None, "same-tool repeats do not trip payload guard")

# Case 4: different blobs through different tools → no trip.
reset_payload_window()
payload_similarity_guard("read_file", BIG)
stop = payload_similarity_guard("write_file", BIG_ALT)
assert_eq(stop, None, "different blobs across read→write do not trip")

# Case 5: bytes payload works same as str.
reset_payload_window()
big_bytes = b"C" * (PAYLOAD_MIN_BYTES + 100)
payload_similarity_guard("read_file", big_bytes)
stop = payload_similarity_guard("write_file", big_bytes)
assert_eq(stop is not None, True, "bytes payload also trips")

# Case 6: non-str/bytes payload (e.g. dict) is a no-op, not an error.
reset_payload_window()
stop = payload_similarity_guard("some_tool", {"big": "dict"})
assert_eq(stop, None, "non-str/bytes payload returns None without error")

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 6 cases passed")
