#!/usr/bin/env python3
"""Live integration tests — run these against the real fleet to verify MCP tools work end-to-end.

Usage:
    python3 tests/test_integration_live.py

Requires: onyx MCP SSH connection reachable (run from ops-agent workspace with MCP active).
These tests call the MCP server via its Python API directly (same path as the real tools).

Each test writes a sentinel file, reads it back, and cleans up. Failure here means the tool
is broken in production — fix before relying on it in sessions.
"""
from __future__ import annotations
import sys
import os

# Add server/ to path so we can import the MCP tools directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

PASS = []
FAIL = []


def check(name: str, result: dict, expect_key: str = "ok", expect_val=True):
    val = result.get(expect_key)
    if val == expect_val:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name} — got {expect_key}={val!r}, error={result.get('error', '')}")


def run():
    print("=== Live integration tests ===\n")

    # Import tools (this also boots transport/run_on)
    try:
        from files import read_file, write_file
        from fleet import fleet_status, tail_logs
        from wp import wp_cli
    except Exception as e:
        print(f"IMPORT FAILED: {e}")
        sys.exit(2)

    # ── fleet_status ────────────────────────────────────────────────────────
    print("fleet_status:")
    r = fleet_status()
    check("fleet_status returns fleet dict", r, "fleet")
    check("main host present", "main" in r.get("fleet", {}))
    check("onyx host present", "onyx" in r.get("fleet", {}))

    # ── read_file (no sudo, readable path) ──────────────────────────────────
    print("\nread_file (no sudo):")
    r = read_file(host="main", path="/var/log/log-scanner.log", tail_lines=5)
    check("read_file log-scanner.log", r)

    # ── read_file (sudo, root-owned log) ────────────────────────────────────
    print("\nread_file (sudo=True):")
    r = read_file(host="main", path="/var/log/server-events.log", tail_lines=5, sudo=True)
    check("read_file server-events.log sudo", r)

    # ── write_file (sudo, /usr/local/bin/) ─────────────────────────────────
    print("\nwrite_file (sudo=True, /usr/local/bin/):")
    sentinel = "# integration-test-sentinel\n"
    test_path = "/usr/local/bin/mcp-integration-test.sh"
    r = write_file(host="main", path=test_path, content=sentinel, sudo=True)
    check("write_file creates sentinel in /usr/local/bin/", r)
    if r.get("ok"):
        # Read it back to confirm
        r2 = read_file(host="main", path=test_path, tail_lines=5, sudo=True)
        check("read back sentinel content", r2)
        check("sentinel content correct", "integration-test-sentinel" in r2.get("content", ""), "ok", True)
        # Clean up
        from transport import run_on
        run_on("main", ["sudo", "-n", "rm", "-f", test_path], timeout=10)

    # ── write_file (sudo, WP mu-plugin path) ───────────────────────────────
    print("\nwrite_file (sudo=True, WP mu-plugin):")
    mu_path = "/var/lib/docker/volumes/ksm_wp-files/_data/wp-content/mu-plugins/mcp-test-sentinel.php"
    r = write_file(host="main", path=mu_path, content="<?php // mcp-integration-test\n", sudo=True)
    check("write_file creates file in ksm mu-plugins", r)
    if r.get("ok"):
        r2 = read_file(host="main", path=mu_path, tail_lines=3, sudo=True)
        check("read back mu-plugin sentinel", r2)
        from transport import run_on
        run_on("main", ["sudo", "-n", "rm", "-f", mu_path], timeout=10)
        # Clean up backup too
        bak = r.get("backup", "")
        if bak:
            run_on("main", ["sudo", "-n", "rm", "-f", bak], timeout=10)

    # ── tail_logs ────────────────────────────────────────────────────────────
    print("\ntail_logs:")
    r = tail_logs(host="main", container="ksm-wp", lines=20)
    check("tail_logs ksm-wp returns lines_analysed", r, "lines_analysed")

    # ── wp_cli (read-only) ───────────────────────────────────────────────────
    print("\nwp_cli:")
    r = wp_cli(host="main", container="ksm-wp", cmd="option get siteurl")
    check("wp_cli option get siteurl", r)
    check("siteurl contains kita-seminar", "kita-seminar" in r.get("output", ""), "ok", True)

    # ── Summary ──────────────────────────────────────────────────────────────
    total = len(PASS) + len(FAIL)
    print(f"\n{'='*40}")
    print(f"Results: {len(PASS)}/{total} passed")
    if FAIL:
        print(f"FAILED: {', '.join(FAIL)}")
        sys.exit(1)
    else:
        print("All integration checks passed.")


if __name__ == "__main__":
    run()
