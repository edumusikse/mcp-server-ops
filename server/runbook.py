"""Runbook + docs tools — lookup, outcome recording, docs, AI cost summary."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from guards import (
    filter_weak_matches as _filter_weak_matches,
    flag_runbook_conflicts as _flag_runbook_conflicts,
)
from state import (
    get_runbooks,
    log_call,
    update_runbook_outcome,
)
from transport import DOCS_DIR, mcp

_AGENT_RUNBOOK = Path("/var/lib/ai-agent/runbook.json")


@mcp.tool()
def read_doc(name: str) -> str:
    """Read an ops context document stored on the control server.

    Available: ops-map, rules, guard-rules, runbook-index

    Args:
        name: Document name
    """
    if name == "runbook-index":
        books = get_runbooks()
        agent_count = 0
        if _AGENT_RUNBOOK.exists():
            try:
                agent_count = len(json.loads(_AGENT_RUNBOOK.read_text()))
            except Exception:
                pass
        summary = {
            "ops_mcp_runbooks": len(books),
            "ai_agent_runbooks": agent_count,
            "entries": [
                {"id": b["id"], "tool": b["tool"], "target": b["target"],
                 "success_count": b["success_count"], "failure_count": b["failure_count"],
                 "needs_review": b["needs_review"]}
                for b in books
            ],
        }
        log_call("read_doc", {"name": "runbook-index"}, summary, 0)
        return json.dumps(summary, indent=2)

    allowed = {
        "ops-map": "ops-map.md",
        "rules": "rules.md",
        "guard-rules": "guard-rules.yaml",
    }
    if name not in allowed:
        return f"Unknown doc '{name}'. Available: {', '.join(allowed)}, runbook-index"
    path = DOCS_DIR / allowed[name]
    if not path.exists():
        return f"Doc '{name}' not found at {path}."
    content = path.read_text()
    log_call("read_doc", {"name": name}, f"{len(content)} chars", 0)
    return content


@mcp.tool()
def lookup_runbook(problem_description: str) -> dict:
    """Search the remediation runbook for known fixes matching a problem description.

    Searches both the ai-remediation-agent runbook (live fixes learned from
    past incidents) and the ops-mcp runbook KB (MCP tool executions).
    Returns entries ranked by success count. Only entries with >=3 successes
    and >=80% success rate are flagged as safe to auto-execute.

    Args:
        problem_description: Free-text description of the problem or symptom
    """
    t0 = time.monotonic()
    keywords = set(problem_description.lower().split())
    results = []

    # Search ai-remediation-agent runbook (JSON array on main server)
    if _AGENT_RUNBOOK.exists():
        try:
            entries = json.loads(_AGENT_RUNBOOK.read_text())
            for e in entries:
                sig = (e.get("problem_signature") or "").lower()
                score = sum(1 for kw in keywords if kw in sig)
                if score > 0:
                    sc = e.get("success_count", 0)
                    fc = e.get("failure_count", 0)
                    total = sc + fc
                    results.append({
                        "source": "ai-agent",
                        "problem_signature": e.get("problem_signature"),
                        "resolution_steps": e.get("commands_used", []),
                        "success_count": sc,
                        "failure_count": fc,
                        "auto_executable": sc >= 3 and (total == 0 or sc / total >= 0.8),
                        "last_used": e.get("last_used"),
                        "match_score": score,
                    })
        except Exception as ex:
            logging.warning("lookup_runbook: agent runbook read error: %s", ex)

    # Search ops-mcp runbook KB
    for rb in get_runbooks():
        sig = (rb.get("target") or "" + rb.get("problem_hint") or "").lower()
        score = sum(1 for kw in keywords if kw in sig)
        if score > 0:
            sc = rb.get("success_count", 0)
            fc = rb.get("failure_count", 0)
            total = sc + fc
            results.append({
                "source": "ops-mcp",
                "id": rb["id"],
                "tool": rb["tool"],
                "target": rb["target"],
                "resolution": json.loads(rb.get("resolution_json") or "{}"),
                "risk_level": rb.get("risk_level"),
                "success_count": sc,
                "failure_count": fc,
                "auto_executable": sc >= 3 and (total == 0 or sc / total >= 0.8),
                "last_used": rb.get("last_used"),
                "match_score": score,
            })

    results.sort(key=lambda x: (-x["match_score"], -x["success_count"]))
    results = _filter_weak_matches(results)
    results = _flag_runbook_conflicts(results)
    ms = round((time.monotonic() - t0) * 1000)
    response = {"matches": results[:10], "total_found": len(results)}
    log_call("lookup_runbook", {"problem_description": problem_description}, response, ms)
    return response


@mcp.tool()
def record_runbook_outcome(runbook_id: str, success: bool, notes: str = "") -> dict:
    """Record whether applying a runbook actually fixed the problem.

    Call this after you apply a runbook returned by lookup_runbook. Passing
    success=False decrements confidence and requeues the entry for review;
    success=True promotes it toward auto_executable status. Without this
    call, bad runbooks never demote and good ones never confirm.

    Args:
        runbook_id: The id from the lookup_runbook match (ops-mcp source only)
        success: True if the runbook fixed the problem, False otherwise
        notes: Optional free-text note (recorded in the audit log)
    """
    t0 = time.monotonic()
    update_runbook_outcome(runbook_id, success)
    ms = round((time.monotonic() - t0) * 1000)
    result = {"ok": True, "runbook_id": runbook_id, "success": success}
    log_call(
        "record_runbook_outcome",
        {"runbook_id": runbook_id, "success": success, "notes": notes},
        result, ms,
        runbook_id=runbook_id,
        verified_outcome="success" if success else "failure",
    )
    return result


@mcp.tool()
def ai_cost_summary(tail: int = 100) -> dict:
    """Return recent AI API call costs from the ai-remediation-agent cost log.

    Each record shows timestamp, model, input/output tokens, and cost in USD.
    Returns the last `tail` records plus a cumulative total.

    Args:
        tail: Number of recent records to return (default 100, max 500)
    """
    t0 = time.monotonic()
    cost_log = Path("/var/lib/ai-agent/cost-log.ndjson")
    if not cost_log.exists():
        return {"error": "Cost log not found — no AI calls have been recorded yet. "
                "The log is written by ai-remediation-agent.py after each Claude API call."}
    tail = min(tail, 500)
    try:
        lines = cost_log.read_text().splitlines()
        records = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        recent = records[-tail:]
        total_in = sum(r.get("input_tokens", 0) for r in records)
        total_out = sum(r.get("output_tokens", 0) for r in records)
        total_cost = sum(r.get("cost_usd", 0) for r in records)
        result = {
            "total_calls": len(records),
            "cumulative": {
                "input_tokens": total_in,
                "output_tokens": total_out,
                "cost_usd": round(total_cost, 4),
            },
            "recent": recent,
        }
    except Exception as e:
        result = {"error": str(e)}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("ai_cost_summary", {"tail": tail}, result, ms)
    return result
