"""Git-based deploy tools — replaces paste-thrash (Bash cat → Read → write_file).

Deploys happen by (1) committing + pushing locally, (2) `git_sync(host)` pulls
latest on the target. Directories not yet under git get `bootstrap_git(host)`
which initialises the repo in place while preserving secrets.

Secrets preserved across bootstrap (kept untracked via repo .gitignore):
  /opt/ops-mcp/.env, /opt/ops-mcp/hosts.yaml
"""
from __future__ import annotations

import logging
import shlex
import time

from state import log_call
from transport import mcp, run_on

DEFAULT_REPO = "https://github.com/edumusikse/mcp-server-ops.git"
DEPLOY_DIR = "/opt/ops-mcp"
_PRESERVE = (".env", "hosts.yaml")


def _preserve_env_and_sync(host: str, repo_url: str, branch: str, sudo: str) -> tuple[int, str]:
    """Shared bootstrap path: init + fetch + checkout while preserving untracked secrets."""
    preserve_expr = " ".join(f"-e {shlex.quote(f)}" for f in _PRESERVE)
    shell = (
        f"set -e; "
        f"cd {shlex.quote(DEPLOY_DIR)}; "
        f"if [ -d .git ]; then echo ALREADY_GIT; exit 2; fi; "
        f"ts=$(date -u +%Y%m%d_%H%M%S); "
        f"{sudo}cp -rp {shlex.quote(DEPLOY_DIR)} {shlex.quote(DEPLOY_DIR)}.bak.$ts; "
        f"{sudo}git init -q -b {shlex.quote(branch)}; "
        f"{sudo}git remote add origin {shlex.quote(repo_url)}; "
        f"{sudo}git fetch -q origin {shlex.quote(branch)}; "
        f"{sudo}git reset -q --hard origin/{shlex.quote(branch)}; "
        f"{sudo}git clean -fdq {preserve_expr}; "
        f"echo BOOTSTRAPPED $(git rev-parse HEAD) backup=$ts"
    )
    return run_on(host, ["sh", "-c", shell], timeout=60)


@mcp.tool()
def bootstrap_git(host: str, repo_url: str = DEFAULT_REPO, branch: str = "main",
                  sudo: bool = True) -> dict:
    """Convert /opt/ops-mcp on `host` into a git clone of `repo_url` in place.

    Safe to run only on a non-git directory. Workflow:
      1. Backup current /opt/ops-mcp to /opt/ops-mcp.bak.<ts>.
      2. git init + remote add origin + fetch origin <branch>.
      3. git reset --hard origin/<branch> (overwrites tracked files).
      4. git clean -fd, preserving .env and hosts.yaml.

    After bootstrap, use git_sync() for all future deploys.

    Args:
        host: Host name from hosts.yaml
        repo_url: Repo URL (default: edumusikse/mcp-server-ops)
        branch: Branch to track (default: main)
        sudo: Use sudo -n (default True — /opt/ops-mcp typically owned by root)
    """
    t0 = time.monotonic()
    args = {"host": host, "repo_url": repo_url, "branch": branch, "sudo": sudo}
    sudo_prefix = "sudo -n " if sudo else ""

    rc, out = _preserve_env_and_sync(host, repo_url, branch, sudo_prefix)
    ok = rc == 0 and "BOOTSTRAPPED" in out
    result = {"ok": ok, "output": out[:2000]}
    if rc == 2 and "ALREADY_GIT" in out:
        result = {"ok": False, "error": "already_git",
                  "message": f"{DEPLOY_DIR} is already a git clone. Use git_sync instead."}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("bootstrap_git", args, result, ms, host=host, needs_review=True)
    logging.info("bootstrap_git %s rc=%d (%dms)", host, rc, ms)
    return result


@mcp.tool()
def git_sync(host: str, branch: str = "main", sudo: bool = True) -> dict:
    """Fetch and hard-reset /opt/ops-mcp on `host` to origin/<branch>.

    The single deploy path. Replaces paste-thrash (Bash cat → Read → write_file).
    Local workflow: edit + commit + push → call git_sync(host) → done.

    Untracked files (.env, hosts.yaml per .gitignore) are preserved.
    The running MCP server holds its code in memory; new invocations pick up
    the new files via stdio per-session spawn.

    Args:
        host: Host name from hosts.yaml
        branch: Branch to sync to (default main)
        sudo: Use sudo -n for git commands (default True)
    """
    t0 = time.monotonic()
    args = {"host": host, "branch": branch, "sudo": sudo}
    sudo_prefix = "sudo -n " if sudo else ""
    preserve_expr = " ".join(f"-e {shlex.quote(f)}" for f in _PRESERVE)

    shell = (
        f"set -e; "
        f"cd {shlex.quote(DEPLOY_DIR)}; "
        f"if [ ! -d .git ]; then echo NOT_GIT; exit 2; fi; "
        f"before=$(git rev-parse HEAD); "
        f"{sudo_prefix}git fetch -q origin {shlex.quote(branch)}; "
        f"after=$(git rev-parse origin/{shlex.quote(branch)}); "
        f"{sudo_prefix}git reset -q --hard origin/{shlex.quote(branch)}; "
        f"{sudo_prefix}git clean -fdq {preserve_expr}; "
        f"echo SYNCED before=$before after=$after"
    )
    rc, out = run_on(host, ["sh", "-c", shell], timeout=60)
    ok = rc == 0 and "SYNCED" in out
    result = {"ok": ok, "output": out[:2000]}
    if rc == 2 and "NOT_GIT" in out:
        result = {"ok": False, "error": "not_git",
                  "message": f"{DEPLOY_DIR} is not a git clone yet. Run bootstrap_git first."}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("git_sync", args, result, ms, host=host, needs_review=True)
    logging.info("git_sync %s rc=%d (%dms)", host, rc, ms)
    return result
