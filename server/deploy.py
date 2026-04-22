"""Git-based deploy tools — replaces paste-thrash (Bash cat → Read → write_file).

Layout mismatch: the repo keeps server code under `server/`, but the live
MCP runs from `/opt/ops-mcp/` directly (where .env, hosts.yaml, .venv and
docs also live). So deploy uses a side clone + file copy rather than making
/opt/ops-mcp itself a git work tree:

    /opt/ops-mcp-repo/        <- git clone, kept pristine
    /opt/ops-mcp/             <- live install (.env, hosts.yaml, .venv, docs)
      server.py                 copied from /opt/ops-mcp-repo/server/server.py
      guards.py, transport.py,  …same

Workflow:
    1. Local edit + commit + push.
    2. MCP call: git_sync(host).
    3. On host: cd /opt/ops-mcp-repo && git fetch + reset --hard origin/main
       then cp -p /opt/ops-mcp-repo/server/*.py /opt/ops-mcp/

Untouched on the deploy target: .env, hosts.yaml, .venv/, docs/, web.py
(web.py stays as-is until split too; update SYNC_FILES when that ships).

First-time setup uses bootstrap_git to create /opt/ops-mcp-repo.
"""
from __future__ import annotations

import logging
import re
import shlex
import time

from state import log_call
from transport import mcp, run_on

DEFAULT_REPO = "https://github.com/edumusikse/mcp-server-ops.git"
REPO_DIR = "/opt/ops-mcp-repo"
DEPLOY_DIR = "/opt/ops-mcp"
VENV_PYTHON = "/opt/ops-mcp/.venv/bin/python3"
# Files in repo's server/ dir that must end up in DEPLOY_DIR.
SYNC_FILES = (
    "server.py", "transport.py", "fleet.py", "wp.py", "compose.py",
    "files.py", "runbook.py", "cloud.py", "deploy.py",
    "guards.py", "state.py",
)

# Kept in lockstep with tests/test_server_imports.py::EXPECTED_TOOLS. A
# silently-dropped @mcp.tool() decorator would still import cleanly, so the
# remote verification checks the registered tool count, not just importability.
EXPECTED_TOOL_COUNT = 20

# Post-sync smoke test: import the just-installed server.py and report tool
# count. A broken split (missing module, bad import, dropped @mcp.tool())
# trips this immediately rather than waiting for the next session to fail.
_VERIFY_PY = (
    "import sys; sys.path.insert(0, '/opt/ops-mcp'); "
    "import server as _s; "
    "tm = getattr(_s.mcp, '_tool_manager', None); "
    "n = len((tm._tools if tm else _s.mcp._tools)); "
    "print(f'IMPORT_OK tools={n}')"
)


def _sync_shell(sudo: str, backup_ts: str) -> str:
    """Shell fragment: copy changed SYNC_FILES from REPO_DIR/server/ to DEPLOY_DIR/.

    For each file: skip if identical; otherwise back up the existing dst to
    <dst>.bak.<backup_ts> (only if dst exists), then install, then emit a
    machine-readable "UPDATED:<file>" marker for the caller to parse.
    Unchanged files are silent — the absence of a marker means no change.
    """
    lines = []
    for f in SYNC_FILES:
        src = shlex.quote(f"{REPO_DIR}/server/{f}")
        dst = shlex.quote(f"{DEPLOY_DIR}/{f}")
        lines.append(
            f"if cmp -s {src} {dst} 2>/dev/null; then :; else "
            f"if [ -e {dst} ]; then {sudo}cp -p {dst} {dst}.bak.{backup_ts}; fi; "
            f"{sudo}install -m 0644 {src} {dst}; "
            f"echo UPDATED:{f}; "
            f"fi"
        )
    return "; ".join(lines)


@mcp.tool()
def bootstrap_git(host: str, repo_url: str = DEFAULT_REPO, branch: str = "main",
                  sudo: bool = True) -> dict:
    """First-time setup: clone the repo to /opt/ops-mcp-repo on `host`.

    Leaves /opt/ops-mcp untouched. After bootstrap, call git_sync to copy
    the server files into place.

    Args:
        host: Host name from hosts.yaml
        repo_url: Repo URL (default: edumusikse/mcp-server-ops)
        branch: Branch to track (default: main)
        sudo: Use sudo -n (default True — /opt/ops-mcp* typically owned by root)
    """
    t0 = time.monotonic()
    args = {"host": host, "repo_url": repo_url, "branch": branch, "sudo": sudo}
    sudo_prefix = "sudo -n " if sudo else ""

    shell = (
        f"set -e; "
        f"if [ -d {shlex.quote(REPO_DIR)}/.git ]; then "
        f"  echo ALREADY_CLONED $({sudo_prefix}git -C {shlex.quote(REPO_DIR)} rev-parse HEAD); "
        f"  exit 0; "
        f"fi; "
        f"{sudo_prefix}git clone -q -b {shlex.quote(branch)} {shlex.quote(repo_url)} {shlex.quote(REPO_DIR)}; "
        f"echo CLONED $({sudo_prefix}git -C {shlex.quote(REPO_DIR)} rev-parse HEAD)"
    )
    rc, out = run_on(host, ["sh", "-c", shell], timeout=60)
    ok = rc == 0 and ("CLONED" in out or "ALREADY_CLONED" in out)
    result = {"ok": ok, "output": out[:2000], "repo_dir": REPO_DIR}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("bootstrap_git", args, result, ms, host=host, needs_review=True)
    logging.info("bootstrap_git %s rc=%d (%dms)", host, rc, ms)
    return result


@mcp.tool()
def git_sync(host: str, branch: str = "main", sudo: bool = True) -> dict:
    """Pull latest to /opt/ops-mcp-repo on `host` and install server files
    into /opt/ops-mcp.

    The single deploy path. Replaces paste-thrash (Bash cat → Read → write_file).
    Local workflow: edit + commit + push → call git_sync(host) → done.

    Files copied are listed in deploy.SYNC_FILES. .env, hosts.yaml, web.py,
    .venv/, docs/ are never touched. The running MCP holds its code in
    memory; new invocations pick up the new files via stdio per-session spawn.

    For each file that actually differs on the target, the previous version
    is preserved at <path>.bak.<backup_ts> before being overwritten. Files
    that already match the repo are left alone (no copy, no backup).

    Post-sync verification imports the installed server and checks the
    registered tool count against EXPECTED_TOOL_COUNT — so a silently-dropped
    @mcp.tool() decorator fails the sync even though import succeeds.

    Returns before/after HEAD, the list of files actually updated, the
    backup timestamp (if any file was replaced), and the observed tool count.

    Args:
        host: Host name from hosts.yaml
        branch: Branch to sync to (default main)
        sudo: Use sudo -n for git + install (default True)
    """
    t0 = time.monotonic()
    args = {"host": host, "branch": branch, "sudo": sudo}
    sudo_prefix = "sudo -n " if sudo else ""
    backup_ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

    verify_cmd = f"{shlex.quote(VENV_PYTHON)} -c {shlex.quote(_VERIFY_PY)}"
    shell = (
        f"set -e; "
        f"if [ ! -d {shlex.quote(REPO_DIR)}/.git ]; then echo NOT_CLONED; exit 2; fi; "
        f"cd {shlex.quote(REPO_DIR)}; "
        f"before=$({sudo_prefix}git rev-parse HEAD); "
        f"{sudo_prefix}git fetch -q origin {shlex.quote(branch)}; "
        f"after=$({sudo_prefix}git rev-parse origin/{shlex.quote(branch)}); "
        f"{sudo_prefix}git reset -q --hard origin/{shlex.quote(branch)}; "
        f"{_sync_shell(sudo_prefix, backup_ts)}; "
        f"echo SYNCED before=$before after=$after; "
        f"echo --- VERIFY ---; "
        f"{verify_cmd} || {{ echo VERIFY_FAIL; exit 3; }}"
    )
    rc, out = run_on(host, ["sh", "-c", shell], timeout=60)

    synced = "SYNCED" in out
    import_match = re.search(r"IMPORT_OK tools=(\d+)", out)
    verified = bool(import_match)
    tool_count = int(import_match.group(1)) if import_match else None
    tool_count_ok = tool_count == EXPECTED_TOOL_COUNT
    files_updated = [
        line[len("UPDATED:"):] for line in out.splitlines()
        if line.startswith("UPDATED:")
    ]
    ok = rc == 0 and synced and verified and tool_count_ok
    result = {
        "ok": ok,
        "output": out[:2000],
        "files_updated": files_updated,
        "backup_ts": backup_ts if files_updated else None,
        "synced": synced,
        "verified": verified,
        "tool_count": tool_count,
        "expected_tool_count": EXPECTED_TOOL_COUNT,
    }
    if rc == 2 and "NOT_CLONED" in out:
        result = {"ok": False, "error": "not_cloned",
                  "message": f"{REPO_DIR} not found. Run bootstrap_git first."}
    elif rc == 3 or (synced and not verified):
        result["error"] = "post_sync_import_failed"
        result["message"] = (
            f"Files synced but `import server` failed on the host. "
            f"The live MCP is now broken. Revert with: "
            f"for f in {' '.join(files_updated) or '<files>'}; do "
            f"sudo mv /opt/ops-mcp/$f.bak.{backup_ts} /opt/ops-mcp/$f; done  "
            f"(or fix the offending module and re-sync)."
        )
    elif verified and not tool_count_ok:
        result["error"] = "post_sync_tool_count_mismatch"
        result["message"] = (
            f"Import succeeded but registered {tool_count} tools — expected "
            f"{EXPECTED_TOOL_COUNT}. A @mcp.tool() decorator may have been "
            f"dropped. Revert with the .bak.{backup_ts} backups or fix the "
            f"offending module and re-sync."
        )
    ms = round((time.monotonic() - t0) * 1000)
    log_call("git_sync", args, result, ms, host=host, needs_review=True)
    logging.info("git_sync %s rc=%d (%dms)", host, rc, ms)
    return result
