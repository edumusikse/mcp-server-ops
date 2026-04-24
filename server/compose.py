"""Docker Compose restart tool — allowlisted stacks only."""
from __future__ import annotations

import logging
import time

from state import log_call
from transport import mcp, run_on

_COMPOSE_STACKS = {
    "edumusik-net", "edumusik-com", "frid", "schafliebe", "evabiallas", "ksm", "kimai",
    "admin-panel",
}


@mcp.tool()
def compose_up(host: str, stack: str) -> dict:
    """Restart a Docker Compose stack with 'docker compose up -d'.

    Only allowlisted stacks can be restarted. Shared infrastructure (traefik,
    shared-infra, monitoring) is not exposed — use break-glass SSH for those.

    Args:
        host: Host name from hosts.yaml
        stack: Stack directory name under /srv/ (e.g. edumusik-net, kimai)
    """
    t0 = time.monotonic()

    if stack not in _COMPOSE_STACKS:
        result = {"ok": False, "error": f"Stack '{stack}' not in allowlist. Allowed: {sorted(_COMPOSE_STACKS)}"}
        log_call("compose_up", {"host": host, "stack": stack}, result, 0, allowed=False, host=host)
        return result

    rc_pre, pre_out = run_on(host, ["sudo", "docker", "compose", "-f", f"/srv/{stack}/docker-compose.yml", "ps", "--format", "{{.Name}}\t{{.Status}}"], timeout=10)
    pre_state = pre_out.strip()

    rc, out = run_on(host, ["sudo", "docker", "compose", "-f", f"/srv/{stack}/docker-compose.yml", "up", "-d"], timeout=60)

    rc_post, post_out = run_on(host, ["sudo", "docker", "compose", "-f", f"/srv/{stack}/docker-compose.yml", "ps", "--format", "{{.Name}}\t{{.Status}}"], timeout=10)
    post_state = post_out.strip()

    verified = rc == 0 and "Up" in post_state
    result = {
        "ok": rc == 0,
        "stack": stack,
        "output": out[:2000],
        "pre_state": pre_state,
        "post_state": post_state,
        "verified": verified,
    }
    ms = round((time.monotonic() - t0) * 1000)
    log_call("compose_up", {"host": host, "stack": stack}, result, ms, host=host)
    logging.info("compose_up %s:%s rc=%d verified=%s (%dms)", host, stack, rc, verified, ms)
    return result
