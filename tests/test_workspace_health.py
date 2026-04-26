#!/usr/bin/env python3
"""Cross-file workspace health checks.

Unit tests prove individual guards work. This harness proves the operational
workspace is coherent: hook wiring order, shared escape-hatch semantics,
documented constants, deploy file coverage, and runbook-first policy.

Run: python3 tests/test_workspace_health.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "server"

failures: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        failures.append(label)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register before exec so dataclasses/typing resolution can find the module.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


settings = json.loads((REPO / ".claude" / "settings.json").read_text())
pre = settings.get("hooks", {}).get("PreToolUse", [])
check(len(pre) >= 3, "PreToolUse has block, runbook_guard, and budget hook groups")


def find_hook_group(hooks_list: list, name_fragment: str) -> dict | None:
    for h in hooks_list:
        if any(name_fragment in hk.get("command", "") for hk in h.get("hooks", [])):
            return h
    return None


block_group = find_hook_group(pre, "block-ssh.py")
runbook_group = find_hook_group(pre, "runbook_guard.py")
budget_group = find_hook_group(pre, "budget_guard.py")

check(block_group is not None and block_group.get("matcher") == "Bash", "block-ssh Bash matcher runs first")
check(block_group is not None and "block-ssh.py" in block_group["hooks"][0]["command"], "first hook is block-ssh.py")
check(runbook_group is not None and runbook_group.get("matcher") == "mcp__ops__.*", "runbook_guard matcher scopes to mcp__ops__*")
check(runbook_group is not None and "runbook_guard.py" in runbook_group["hooks"][0]["command"], "second hook is runbook_guard.py")
budget_matcher = budget_group.get("matcher", "") if budget_group else ""
check("mcp__ops__" in budget_matcher, "budget_guard matcher covers all tools")
check(budget_group is not None and "budget_guard.py" in budget_group["hooks"][0]["command"], "third hook is budget_guard.py")
if block_group and runbook_group and budget_group:
    check(pre.index(block_group) < pre.index(runbook_group), "block-ssh runs before runbook_guard")
    check(pre.index(runbook_group) < pre.index(budget_group), "runbook_guard runs before budget_guard")

for hook in (
    REPO / ".claude/hooks/block-ssh.py",
    REPO / ".claude/hooks/runbook_guard.py",
    REPO / ".claude/hooks/budget_guard.py",
    REPO / ".claude/hooks/plan_first_guard.py",
):
    check(hook.exists(), f"{hook.name} exists")
    check(os.access(hook, os.X_OK), f"{hook.name} executable")

find_guard_group = find_hook_group(pre, "find-guard.py")
check(find_guard_group is not None, "find-guard.py is wired in PreToolUse")
check(find_guard_group is not None and find_guard_group.get("matcher") == "Bash", "find-guard Bash matcher")
if find_guard_group and block_group and find_guard_group is block_group:
    bash_hooks = block_group.get("hooks", [])
    block_idx = next((i for i, h in enumerate(bash_hooks) if "block-ssh.py" in h.get("command", "")), None)
    find_idx  = next((i for i, h in enumerate(bash_hooks) if "find-guard.py" in h.get("command", "")), None)
    check(block_idx is not None and find_idx is not None and block_idx < find_idx,
          "block-ssh.py runs before find-guard.py in Bash hooks")

for hook in (
    REPO / ".claude/hooks/find-guard.py",
    REPO / ".claude/known-paths.md",
):
    check(hook.exists(), f"{hook.name} exists")
check(os.access(REPO / ".claude/hooks/find-guard.py", os.X_OK), "find-guard.py executable")

block_ssh = load_module("block_ssh_health", REPO / ".claude/hooks/block-ssh.py")
budget = load_module("budget_guard_health", REPO / ".claude/hooks/budget_guard.py")
runbook_guard = load_module("runbook_guard_health", REPO / ".claude/hooks/runbook_guard.py")
find_guard = load_module("find_guard_health", REPO / ".claude/hooks/find-guard.py")

check(
    block_ssh.BYPASS_FILE == budget.BYPASS_FILE == runbook_guard.BYPASS_FILE,
    "hooks share one bypass file",
)
check(
    block_ssh.BYPASS_TTL_SEC == budget.BYPASS_TTL_SEC == runbook_guard.BYPASS_TTL_SEC == 300,
    "hooks share 300s bypass TTL",
)
check(
    block_ssh.BYPASS_TOKEN == budget.BYPASS_TOKEN == runbook_guard.BYPASS_TOKEN == "CONFIRMED",
    "hooks share CONFIRMED token",
)
kill_switches = {block_ssh.KILL_SWITCH, budget.KILL_SWITCH, runbook_guard.KILL_SWITCH}
check(len(kill_switches) == 3, "hooks have three distinct permanent kill switches")

for cmd in ("find . -name '*.py'", "grep -rl foo src/", "grep -rn bar ."):
    check(find_guard.is_search_command(cmd), f"find-guard intercepts: {cmd!r}")
for cmd in ("ls -la", "cat file.txt", "python3 test.py"):
    check(not find_guard.is_search_command(cmd), f"find-guard ignores: {cmd!r}")

compliance = load_module("runbook_compliance_health", REPO / "tests/runbook_compliance.py")
check(
    set(runbook_guard.RUNBOOK_EXEMPT_TOOLS) == set(compliance.RUNBOOK_EXEMPT_TOOLS),
    "runbook_guard exempt set matches runbook_compliance analyzer",
)
check(
    runbook_guard.RUNBOOK_TOOL == compliance.RUNBOOK_TOOL,
    "runbook_guard and compliance analyzer agree on the runbook tool name",
)

blocked_samples = [
    "ssh edumusik-net uptime",
    "printf ok; ssh edumusik-net uptime",
    "sudo -n docker ps",
    "env KUBECONFIG=/tmp/k kubectl get pods",
]
for sample in blocked_samples:
    check(block_ssh.decide(sample, kill=False, bypass=False)["decision"] == "block",
          f"block-ssh blocks {sample!r}")
check(block_ssh.decide("ssh onyx-bash uptime", kill=False, bypass=False)["level"] == "fallback",
      "block-ssh preserves onyx-bash fallback")

guards_text = (SERVER / "guards.py").read_text()
claude = (REPO / "CLAUDE.md").read_text()
project_server_skill = (REPO / ".claude/skills/server/SKILL.md").read_text()

def const_int(name: str, text: str) -> int:
    m = re.search(rf"^{name}\s*=\s*(.+)$", text, re.M)
    if not m:
        raise AssertionError(f"missing constant {name}")
    expr = m.group(1).strip().replace("_", "")
    if "*" in expr:
        total = 1
        for part in expr.split("*"):
            total *= int(part.strip())
        return total
    return int(expr)


check(const_int("THRASH_LIMIT", guards_text) == 5, "THRASH_LIMIT is 5")
check(const_int("PAYLOAD_SIM_LIMIT", guards_text) == 2, "PAYLOAD_SIM_LIMIT is 2")
check(const_int("PAYLOAD_MIN_BYTES", guards_text) == 8 * 1024, "PAYLOAD_MIN_BYTES is 8KB")
check(budget.DEFAULT_TIME_CAP_MIN == 30, "budget default time is 30 min")
check(budget.DEFAULT_TOKEN_CAP == 100_000, "budget default output cap is 100k")

doc_claims = [
    ("5+ consecutive", "CLAUDE.md documents thrash threshold"),
    ("2 distinct tools", "CLAUDE.md documents payload threshold"),
    ("100k output tokens OR 30 min", "CLAUDE.md documents budget caps"),
    ("before any operational action", "CLAUDE.md documents strict runbook-first policy"),
    ("tests/audit.sh", "CLAUDE.md documents single health gate"),
]
for needle, label in doc_claims:
    check(needle in claude, label)
check("lookup_runbook" in project_server_skill and "before any operational" in project_server_skill,
      "project server skill documents runbook-first policy")

deploy_text = (SERVER / "deploy.py").read_text()

def literal_assignment(name: str, text: str):
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"missing assignment {name}")


sync_files = set(literal_assignment("SYNC_FILES", deploy_text))
expected_sync = {
    "server.py", "transport.py", "fleet.py", "wp.py", "compose.py",
    "files.py", "runbook.py", "cloud.py", "deploy.py", "guards.py", "state.py",
}
check(sync_files == expected_sync, "git_sync SYNC_FILES covers every deployed server module")

test_imports = (REPO / "tests/test_server_imports.py").read_text()
expected_tools_match = re.search(r"EXPECTED_TOOLS\s*=\s*\{(?P<body>.*?)\n\}", test_imports, re.S)
check(bool(expected_tools_match), "EXPECTED_TOOLS set is present")
if expected_tools_match:
    expected_tool_count = len(re.findall(r'"[a-z_]+"', expected_tools_match.group("body")))
    deploy_tool_count = literal_assignment("EXPECTED_TOOL_COUNT", deploy_text)
    check(deploy_tool_count == expected_tool_count,
          "deploy.EXPECTED_TOOL_COUNT matches pinned EXPECTED_TOOLS")

runbook_text = (SERVER / "runbook.py").read_text()
compliance_text = (REPO / "tests/runbook_compliance.py").read_text()
for name in ("lookup_runbook", "record_runbook_outcome", "read_doc"):
    check(f"def {name}" in runbook_text, f"{name} tool exists")
check('RUNBOOK_TOOL = "mcp__ops__lookup_runbook"' in compliance_text,
      "runbook_compliance tracks lookup_runbook")
check("runbook_missed" in compliance_text and "runbook_late" in compliance_text,
      "runbook_compliance detects missed and late lookups")

audit = (REPO / "tests/audit.sh").read_text()
for test_name in (
    "test_budget_guard.py",
    "test_payload_guard.py",
    "test_thrash_guard.py",
    "test_runbook_hygiene.py",
    "test_runbook_compliance.py",
    "test_runbook_guard.py",
    "test_server_imports.py",
    "test_block_ssh.py",
    "test_workspace_health.py",
):
    check(test_name in audit, f"audit.sh runs {test_name}")

# --- server-config: deployed scripts must be executable ---
server_config = REPO / "server-config"
if server_config.is_dir():
    non_exec = []
    for pattern in ("*/usr/local/bin/*.sh", "scripts/*.sh", "wp-nginx/*.sh"):
        for p in sorted(server_config.glob(pattern)):
            if "/etc/" not in str(p) and not os.access(p, os.X_OK):
                non_exec.append(str(p.relative_to(REPO)))
    check(
        not non_exec,
        f"server-config shell scripts are executable"
        + (f": missing +x on {non_exec[:3]}{'...' if len(non_exec) > 3 else ''}" if non_exec else ""),
    )

if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: workspace health checks passed")
