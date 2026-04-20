"""Shared transport primitives — env bootstrap, FLEET config, SSH dispatch, MCP instance.

Every tool module imports `mcp` from here and uses `@mcp.tool()` to register.
server.py imports every tool module to trigger registration, then calls mcp.run().
"""
from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path

import yaml

# ── Bootstrap: load .env before anything else ────────────────────────────────

_ENV_FILE = Path(os.environ.get("OPS_ENV_FILE", "/opt/ops-mcp/.env"))
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Logging (file only — stdout is MCP transport) ────────────────────────────

_LOG_DIR = Path(os.environ.get("OPS_STATE_DIR", str(Path.home() / ".ops-mcp")))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(_LOG_DIR / "ops-mcp.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ── MCP instance ──────────────────────────────────────────────────────────────

from mcp.server.fastmcp import FastMCP  # noqa: E402

_MCP_NAME = os.environ.get("OPS_MCP_NAME", "ops")
mcp = FastMCP(_MCP_NAME)

# ── Fleet config ──────────────────────────────────────────────────────────────

_HOSTS_FILE = Path(os.environ.get("OPS_HOSTS_FILE", "/opt/ops-mcp/hosts.yaml"))
FLEET: dict = {}
if _HOSTS_FILE.exists():
    _data = yaml.safe_load(_HOSTS_FILE.read_text()) or {}
    FLEET = _data.get("fleet", {})
    logging.info("Fleet loaded: %s", list(FLEET))
else:
    logging.warning("hosts.yaml not found at %s", _HOSTS_FILE)

DOCS_DIR = Path("/opt/ops-mcp/docs")

# ── Command dispatch ──────────────────────────────────────────────────────────

_BANNER_LINES = frozenset([
    "authorised access only. all activity is monitored and logged.",
    "unauthorised access is prohibited and will be prosecuted.",
])


def strip_banner(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if line.strip().lower() not in _BANNER_LINES
    ).strip()


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Run a command locally."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as e:
        return 1, str(e)


def run_on(host: str, cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Run a command on a fleet host: local if ssh is null, otherwise via private SSH."""
    cfg = FLEET.get(host)
    if cfg is None:
        return 1, f"Unknown host '{host}'. Known: {list(FLEET)}"

    ssh_addr = cfg.get("ssh")
    if ssh_addr is None:
        return run(cmd, timeout=timeout)

    user = cfg.get("user", "")
    target = f"{user}@{ssh_addr}" if user else ssh_addr
    ssh_cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no"]
    if cfg.get("identity_file"):
        ssh_cmd += ["-i", cfg["identity_file"]]
    ssh_cmd += [target, shlex.join(cmd)]
    rc, out = run(ssh_cmd, timeout=timeout + 6)
    return rc, strip_banner(out)


def allowlist(host: str) -> set[str]:
    cfg = FLEET.get(host, {})
    items = cfg.get("restart_allowlist", [])
    return {s.strip() for s in items if isinstance(s, str)}
