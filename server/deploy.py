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
import shlex
import time

from state import log_call
from transport import mcp, run_on

DEFAULT_REPO = "https://github.com/edumusikse/mcp-server-ops.git"
REPO_DIR = "/opt/ops-mcp-repo"
DEPLOY_DIR = "/opt/ops-mcp"
# Files in repo's server/ dir that must end up in DEPLOY_DIR.
SYNC_FILES = (
    "server.py", "transport.py", "fleet.py", "wp.py", "compose.py",
    "files.py", "runbook.py", "cloud.py", "deploy.py",
    "guards.py", "state.py",
)


def _sync_shell(sudo: str) -> str:
    """Shell fragment: copy SYNC_FILES from REPO_DIR/server/ to DEPLOY_DIR/."""
    lines = []
    for f in SYNC_FILES:
        src = shlex.quote(f"{REPO_DIR}/server/{f}")
        dst = shlex.quote(f"{DEPLOY_DIR}/{f}")
        lines.append(f"{sudo}install -m 0644 -C {src} {dst}")
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
        f"  echo ALREADY_CLONED $(cd {shlex.quote(REPO_DIR)} && git rev-parse HEAD); "
        f"  exit 0; "
        f"fi; "
        f"{sudo_prefix}git clone -q -b {shlex.quote(branch)} {shlex.quote(repo_url)} {shlex.quote(REPO_DIR)}; "
        f"cd {shlex.quote(REPO_DIR)}; "
        f"echo CLONED $(git rev-parse HEAD)"
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

    Returns before/after HEAD and the list of files actually updated.

    Args:
        host: Host name from hosts.yaml
        branch: Branch to sync to (default main)
        sudo: Use sudo -n for git + install (default True)
    """
    t0 = time.monotonic()
    args = {"host": host, "branch": branch, "sudo": sudo}
    sudo_prefix = "sudo -n " if sudo else ""

    shell = (
        f"set -e; "
        f"if [ ! -d {shlex.quote(REPO_DIR)}/.git ]; then echo NOT_CLONED; exit 2; fi; "
        f"cd {shlex.quote(REPO_DIR)}; "
        f"before=$(git rev-parse HEAD); "
        f"{sudo_prefix}git fetch -q origin {shlex.quote(branch)}; "
        f"after=$(git rev-parse origin/{shlex.quote(branch)}); "
        f"{sudo_prefix}git reset -q --hard origin/{shlex.quote(branch)}; "
        f"{_sync_shell(sudo_prefix)}; "
        f"echo SYNCED before=$before after=$after"
    )
    rc, out = run_on(host, ["sh", "-c", shell], timeout=60)
    ok = rc == 0 and "SYNCED" in out
    result = {"ok": ok, "output": out[:2000], "files_synced": list(SYNC_FILES)}
    if rc == 2 and "NOT_CLONED" in out:
        result = {"ok": False, "error": "not_cloned",
                  "message": f"{REPO_DIR} not found. Run bootstrap_git first."}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("git_sync", args, result, ms, host=host, needs_review=True)
    logging.info("git_sync %s rc=%d (%dms)", host, rc, ms)
    return result
