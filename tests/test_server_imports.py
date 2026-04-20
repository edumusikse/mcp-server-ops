#!/usr/bin/env python3
"""Smoke test for the split server — every topic module imports, every
expected tool registers, no extras leak in.

Catches: module rename without entry-point update, dropped @mcp.tool()
decorator, accidental new tool that wasn't documented, FastMCP import
breakage. Runs without a real `mcp` install via a tiny stub on PYTHONPATH.

Run: `python3 tests/test_server_imports.py`
"""
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "server"

# Stub `mcp` so we can import without the real FastMCP package installed.
_STUB = tempfile.mkdtemp(prefix="mcp-stub-")
(Path(_STUB) / "mcp" / "server").mkdir(parents=True)
(Path(_STUB) / "mcp" / "__init__.py").write_text("")
(Path(_STUB) / "mcp" / "server" / "__init__.py").write_text("")
(Path(_STUB) / "mcp" / "server" / "fastmcp.py").write_text(
    "class FastMCP:\n"
    "    def __init__(self, name):\n"
    "        self.name = name; self._tools = {}\n"
    "    def tool(self):\n"
    "        def deco(fn):\n"
    "            self._tools[fn.__name__] = fn\n"
    "            return fn\n"
    "        return deco\n"
    "    def run(self, transport=None):\n"
    "        pass\n"
)

sys.path.insert(0, _STUB)
sys.path.insert(0, str(SERVER))

# Point env-bootstrap at non-existent files so transport.py doesn't try to
# read /opt/ops-mcp/.env or hosts.yaml on the test machine.
os.environ["OPS_ENV_FILE"] = "/tmp/__nope__.env"
os.environ["OPS_HOSTS_FILE"] = "/tmp/__nope__.yaml"
os.environ["OPS_STATE_DIR"] = tempfile.mkdtemp(prefix="ops-state-test-")

EXPECTED_TOOLS = {
    # fleet.py
    "server_status", "fleet_status", "list_containers", "tail_logs",
    "safe_restart", "describe_server", "systemctl_restart",
    # wp.py
    "wp_cli",
    # compose.py
    "compose_up",
    # files.py
    "read_file", "write_file",
    # runbook.py
    "lookup_runbook", "record_runbook_outcome", "read_doc", "ai_cost_summary",
    # cloud.py
    "hetzner_firewall", "cloudflare_dns",
    # deploy.py
    "git_sync", "bootstrap_git",
}

failures: list[str] = []


def assert_eq(actual, expected, label: str) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


# Case 1: server.py imports cleanly (every topic module loads, every
# decorator runs).
import server  # noqa: E402

# Case 2: the registered tool set matches EXPECTED_TOOLS exactly — no
# missing tools, no surprise additions.
got = set(server.mcp._tools.keys())
missing = EXPECTED_TOOLS - got
extra = got - EXPECTED_TOOLS
assert_eq(missing, set(), "missing tools")
assert_eq(extra, set(), "unexpected tools")

# Case 3: every tool function has a docstring (FastMCP uses it for the
# tool description shown to the model — silent doc rot is a real failure
# mode).
no_doc = sorted(name for name, fn in server.mcp._tools.items() if not (fn.__doc__ or "").strip())
assert_eq(no_doc, [], "tools missing docstring")

# Case 4: shared mcp instance — every tool is registered against the SAME
# FastMCP, not a separate instance per module (would happen if a module
# accidentally did `mcp = FastMCP(...)` instead of importing).
from transport import mcp as transport_mcp  # noqa: E402
assert_eq(transport_mcp is server.mcp, True, "tools registered on the shared mcp instance")

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print(f"OK: 4 cases passed ({len(got)} tools registered)")
