#!/usr/bin/env python3
"""Tests for .claude/hooks/block-ssh.py.

Coverage:
    - decide() precedence: kill > bypass > fallback > block
    - blocked shell segments match ssh/sftp/scp/rsync/docker/kubectl
      even after separators or sudo/env wrappers
    - onyx-bash fallback allows ssh/sftp/scp/rsync on that alias
    - first-token CONFIRMED bypass parsing (same as budget_guard)
    - malformed stdin → exit 0 (fail-open)
    - kill switch presence → exit 0 with context envelope

Subprocess cases mirror the budget_guard test pattern — we invoke the hook
as a real CLI and assert exit codes + stderr/stdout.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "block-ssh.py"
BYPASS_FILE = "/tmp/claude-hook-bypass"

spec = importlib.util.spec_from_file_location("block_ssh_mod", HOOK)
block_ssh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block_ssh)

failures: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        failures.append(label)


def run_hook(payload: dict, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def suspend_kill_switch() -> Path | None:
    """Rename ~/.ops-mcp/block-ssh-off aside so subprocess tests exercise real logic."""
    ks = block_ssh.KILL_SWITCH
    if ks.exists():
        stash = ks.with_suffix(".stash")
        ks.rename(stash)
        return stash
    return None


def restore_kill_switch(stash: Path | None) -> None:
    if stash and stash.exists():
        stash.rename(block_ssh.KILL_SWITCH)


def clear_bypass() -> None:
    try:
        os.unlink(BYPASS_FILE)
    except FileNotFoundError:
        pass


# ─── Pure decide() cases ──────────────────────────────────────────────────

# C1: plain ssh blocks
r = block_ssh.decide("ssh server uptime", kill=False, bypass=False)
check(r["decision"] == "block" and r["level"] == "hard", "C1 plain ssh blocks")

# C2: onyx-bash fallback allows
r = block_ssh.decide("ssh onyx-bash uptime", kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "fallback", "C2 onyx-bash fallback")

# C3: docker blocks
r = block_ssh.decide("docker ps", kill=False, bypass=False)
check(r["decision"] == "block", "C3 docker blocks")

# C4: kubectl blocks
r = block_ssh.decide("kubectl get pods", kill=False, bypass=False)
check(r["decision"] == "block", "C4 kubectl blocks")

# C5: non-matching command allows
r = block_ssh.decide("ls -la", kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "ok", "C5 plain ls allows")

# C6: bypass overrides block
r = block_ssh.decide("ssh server uptime", kill=False, bypass=True)
check(r["decision"] == "allow" and r["level"] == "bypass", "C6 bypass overrides block")

# C7: kill switch overrides everything
r = block_ssh.decide("ssh server uptime", kill=True, bypass=False)
check(r["decision"] == "allow" and r["level"] == "kill", "C7 kill overrides block")

# C8: kill precedence over bypass
r = block_ssh.decide("ssh server uptime", kill=True, bypass=True)
check(r["decision"] == "allow" and r["level"] == "kill", "C8 kill > bypass precedence")

# C9: sftp onyx-bash allowed
r = block_ssh.decide("sftp onyx-bash:/tmp/file /tmp/", kill=False, bypass=False)
check(r["decision"] == "allow" and r["level"] == "fallback", "C9 sftp onyx-bash fallback")

# C9b: direct ssh after a shell separator still blocks
r = block_ssh.decide("printf ok; ssh server uptime", kill=False, bypass=False)
check(r["decision"] == "block", "C9b semicolon ssh blocks")

# C9c: sudo/docker wrappers still block
r = block_ssh.decide("sudo -n docker ps", kill=False, bypass=False)
check(r["decision"] == "block", "C9c sudo docker blocks")

# C9d: env/kubectl wrappers still block
r = block_ssh.decide("env KUBECONFIG=/tmp/k kubectl get pods", kill=False, bypass=False)
check(r["decision"] == "block", "C9d env kubectl blocks")

# C9e: text mentioning ssh is not itself a shell command segment
r = block_ssh.decide("printf 'ssh server uptime'", kill=False, bypass=False)
check(r["decision"] == "allow", "C9e quoted mention allows")

# ─── Bypass file parsing ──────────────────────────────────────────────────

clear_bypass()
check(block_ssh.bypass_active() is False, "C10 no bypass file → inactive")

# C11: exact "CONFIRMED"
with open(BYPASS_FILE, "w") as f:
    f.write("CONFIRMED")
check(block_ssh.bypass_active() is True, "C11 CONFIRMED exact")

# C12: "CONFIRMED # comment" (first-token match, same as budget_guard)
with open(BYPASS_FILE, "w") as f:
    f.write("CONFIRMED # 5-min unblock")
check(block_ssh.bypass_active() is True, "C12 CONFIRMED with comment (first-token)")

# C13: expired bypass
with open(BYPASS_FILE, "w") as f:
    f.write("CONFIRMED")
old_ts = time.time() - (block_ssh.BYPASS_TTL_SEC + 60)
os.utime(BYPASS_FILE, (old_ts, old_ts))
check(block_ssh.bypass_active() is False, "C13 expired bypass rejected")

# C14: wrong token
with open(BYPASS_FILE, "w") as f:
    f.write("YES")
check(block_ssh.bypass_active() is False, "C14 wrong token rejected")

clear_bypass()

# ─── Subprocess end-to-end ────────────────────────────────────────────────

stash = suspend_kill_switch()
try:
    # C15: blocked command → exit 2, stderr reason
    clear_bypass()
    p = run_hook({"tool_input": {"command": "ssh server uptime"}})
    check(p.returncode == 2, "C15 block exits 2")
    check("Direct SSH" in p.stderr, "C15 block reason in stderr")

    # C16: allowed command → exit 0
    p = run_hook({"tool_input": {"command": "ls"}})
    check(p.returncode == 0, "C16 allow exits 0")

    # C17: bypass file active → block lifted, context emitted
    with open(BYPASS_FILE, "w") as f:
        f.write("CONFIRMED")
    p = run_hook({"tool_input": {"command": "ssh server uptime"}})
    check(p.returncode == 0, "C17 bypass lifts block")
    check("SSH-BLOCK BYPASS active" in p.stdout, "C17 bypass context emitted")
    clear_bypass()

    # C18: malformed JSON → fail-open (exit 0)
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        timeout=10,
    )
    check(r.returncode == 0, "C18 malformed stdin exits 0 (fail-open)")

    # C19: missing tool_input.command → allow
    p = run_hook({"tool_input": {}})
    check(p.returncode == 0, "C19 missing command allows")
finally:
    restore_kill_switch(stash)

# C20: kill switch present → allow + kill-context
ks = block_ssh.KILL_SWITCH
ks.parent.mkdir(parents=True, exist_ok=True)
ks_stash = suspend_kill_switch()
try:
    ks.touch()
    p = run_hook({"tool_input": {"command": "ssh server uptime"}})
    check(p.returncode == 0, "C20 kill switch lifts block")
    check("KILL SWITCH" in p.stdout, "C20 kill context emitted")
finally:
    if ks.exists():
        ks.unlink()
    restore_kill_switch(ks_stash)


if failures:
    print("FAIL:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
print("OK: 24 cases passed")
