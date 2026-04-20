#!/usr/bin/env python3
"""
ops-mcp: Fleet control server — one process manages the whole fleet via SSH over LAN.

Runs on the control server. Managed hosts are reached via private network SSH (zero egress cost).
Tools take a `host` parameter; fleet_status() queries all hosts in parallel.

Credentials: /opt/ops-mcp/.env (chmod 600, never in git)
Fleet config: /opt/ops-mcp/hosts.yaml

Transport: stdio
Connect via: ssh control-server /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/server.py

NEVER print to stdout — that is the JSON-RPC transport channel.

This file is the thin entry point. Tool definitions live in topic modules:
  transport.py   shared mcp + FLEET + run_on + env bootstrap
  fleet.py       server_status, fleet_status, list_containers, tail_logs,
                 safe_restart, describe_server, systemctl_restart
  wp.py          wp_cli
  compose.py     compose_up
  files.py       read_file, write_file  (+ payload-similarity guard)
  runbook.py     lookup_runbook, record_runbook_outcome, read_doc, ai_cost_summary
  cloud.py       hetzner_firewall, cloudflare_dns
  deploy.py      git_sync, bootstrap_git   (replaces paste-thrash)
"""
from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, "/opt/ops-mcp")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import init_db  # noqa: E402
from transport import FLEET, mcp  # noqa: E402

# Importing these modules is what registers the @mcp.tool() decorators.
import fleet      # noqa: F401, E402
import wp         # noqa: F401, E402
import compose    # noqa: F401, E402
import files      # noqa: F401, E402
import runbook    # noqa: F401, E402
import cloud      # noqa: F401, E402
import deploy     # noqa: F401, E402


if __name__ == "__main__":
    init_db()
    logging.info("ops-mcp starting (fleet=%s, pid=%d)", list(FLEET), os.getpid())
    mcp.run(transport="stdio")
