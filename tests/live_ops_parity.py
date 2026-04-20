#!/usr/bin/env python3
"""Parity check: local expectations vs deployed /opt/ops-mcp.

Two modes:

    1. Static parity (default, always runs). Pure local checks — no network.
       * SYNC_FILES in server/deploy.py exists as a set of files under server/.
       * EXPECTED_TOOL_COUNT in server/deploy.py matches the size of
         EXPECTED_TOOLS in tests/test_server_imports.py.
       * git HEAD is reachable (for HEAD comparison in live mode).
       (The docs/ directory lives only on onyx at /opt/ops-mcp/docs/ — it
       is not synced locally, so the docs check is live-only.)

    2. Live parity (--live or --host onyx). Uses the onyx-bash ssh alias
       (the non-FIDO fallback path — see block-ssh.py) to inspect
       /opt/ops-mcp and /opt/ops-mcp-repo. Compares:
         * Each SYNC_FILES entry present in /opt/ops-mcp/
         * Live tool count matches EXPECTED_TOOL_COUNT
         * Live git HEAD matches local git HEAD (or records divergence)
         * docs present at /opt/ops-mcp/docs/

       If the ssh invocation fails for any reason (host unreachable, key not
       loaded, command timeout), --live exits 0 with a `skipped` report
       unless --strict-live is set.

Exit codes:
    0 = all static checks passed; live section (if requested) either passed
        or was skipped non-strictly
    1 = any check failed (or live was requested with --strict-live and could
        not complete)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_HOST_ALIAS = "onyx-bash"
DEPLOY_DIR = "/opt/ops-mcp"
REPO_DIR = "/opt/ops-mcp-repo"


def read_literal_assignment(name: str, text: str):
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"missing assignment {name}")


def static_checks() -> list[tuple[bool, str]]:
    results: list[tuple[bool, str]] = []
    deploy_text = (REPO / "server" / "deploy.py").read_text()
    sync_files = list(read_literal_assignment("SYNC_FILES", deploy_text))
    expected_tool_count = read_literal_assignment("EXPECTED_TOOL_COUNT", deploy_text)

    for f in sync_files:
        path = REPO / "server" / f
        results.append((path.is_file(), f"server/{f} present locally"))

    imports_text = (REPO / "tests" / "test_server_imports.py").read_text()
    m = re.search(r"EXPECTED_TOOLS\s*=\s*\{(?P<body>.*?)\n\}", imports_text, re.S)
    if not m:
        results.append((False, "EXPECTED_TOOLS set missing from test_server_imports.py"))
    else:
        expected_tools_count = len(re.findall(r'"[a-z_]+"', m.group("body")))
        results.append((
            expected_tool_count == expected_tools_count,
            f"deploy.EXPECTED_TOOL_COUNT ({expected_tool_count}) == "
            f"len(EXPECTED_TOOLS) ({expected_tools_count})",
        ))

    head_rc = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=5,
    )
    results.append((head_rc.returncode == 0, "local git HEAD resolvable"))
    return results


def ssh_probe(host_alias: str, shell_cmd: str, timeout: int = 15) -> tuple[int, str, str]:
    """Invoke ssh on the given alias with a single shell command.

    Isolated in a helper so the live_checks() function stays test-friendly.
    """
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
         host_alias, "sh", "-c", shell_cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def live_checks(host_alias: str) -> tuple[list[tuple[bool, str]], str | None]:
    """Return (results, error). If error is not None, the live section was skipped."""
    deploy_text = (REPO / "server" / "deploy.py").read_text()
    sync_files = list(read_literal_assignment("SYNC_FILES", deploy_text))
    expected_tool_count = read_literal_assignment("EXPECTED_TOOL_COUNT", deploy_text)

    # Single round-trip: list SYNC_FILES presence, docs dir, git HEAD, and
    # invoke the venv python to count tools. All output is one JSON blob.
    file_checks = " ".join(
        f'echo {shlex.quote(f)}:$([ -f {shlex.quote(f"{DEPLOY_DIR}/{f}")} ] && echo 1 || echo 0)'
        for f in sync_files
    )
    verify_py = (
        "import sys; sys.path.insert(0, '/opt/ops-mcp'); "
        "import server as _s; "
        "tm = getattr(_s.mcp, '_tool_manager', None); "
        "n = len((tm._tools if tm else _s.mcp._tools)); "
        "print(f'tool_count={n}')"
    )
    shell_cmd = (
        f"{file_checks}; "
        f"echo docs_ops_map:$([ -f {shlex.quote(f'{DEPLOY_DIR}/docs/ops-map.md')} ] || "
        f"  [ -f {shlex.quote(f'{DEPLOY_DIR}/docs/ops-map.yaml')} ] && echo 1 || echo 0); "
        f"echo live_head:$(git -C {shlex.quote(REPO_DIR)} rev-parse HEAD 2>/dev/null || echo none); "
        f"/opt/ops-mcp/.venv/bin/python3 -c {shlex.quote(verify_py)} 2>/dev/null || echo tool_count=0"
    )
    try:
        rc, out, err = ssh_probe(host_alias, shell_cmd)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return [], f"ssh {host_alias}: {e}"
    if rc != 0:
        return [], f"ssh {host_alias} exited {rc}: {err.strip()[:200]}"

    lines = {
        k: v for k, v in
        (line.split(":", 1) for line in out.splitlines() if ":" in line)
    }

    results: list[tuple[bool, str]] = []
    for f in sync_files:
        results.append((lines.get(f) == "1", f"live: {DEPLOY_DIR}/{f} present"))
    results.append((lines.get("docs_ops_map") == "1", f"live: {DEPLOY_DIR}/docs/ops-map present"))

    m = re.search(r"tool_count=(\d+)", out)
    live_tool_count = int(m.group(1)) if m else 0
    results.append((
        live_tool_count == expected_tool_count,
        f"live tool count ({live_tool_count}) == EXPECTED_TOOL_COUNT ({expected_tool_count})",
    ))

    live_head = lines.get("live_head", "none")
    local_head = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=5,
    ).stdout.strip()
    results.append((
        live_head == local_head,
        f"live HEAD ({live_head[:12]}) == local HEAD ({local_head[:12]})",
    ))
    return results, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--live", action="store_true", help="Run live SSH parity against --host")
    ap.add_argument("--host", default=DEFAULT_HOST_ALIAS, help="SSH alias for live mode")
    ap.add_argument("--strict-live", action="store_true",
                    help="Fail (exit 1) if --live requested and ssh fails")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    static_results = static_checks()
    static_fail = [label for ok, label in static_results if not ok]

    live_results: list[tuple[bool, str]] = []
    live_error: str | None = None
    live_fail: list[str] = []
    live_requested = args.live or (args.host != DEFAULT_HOST_ALIAS) or args.strict_live
    if live_requested:
        live_results, live_error = live_checks(args.host)
        live_fail = [label for ok, label in live_results if not ok]

    report = {
        "static_checks": len(static_results),
        "static_fail": static_fail,
        "live_requested": live_requested,
        "live_skipped": live_requested and live_error is not None,
        "live_error": live_error,
        "live_checks": len(live_results),
        "live_fail": live_fail,
    }
    if args.pretty:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        json.dump(report, sys.stdout)
        sys.stdout.write("\n")

    if static_fail:
        return 1
    if live_error and args.strict_live:
        return 1
    if live_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
