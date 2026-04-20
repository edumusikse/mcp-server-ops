#!/usr/bin/env python3
"""Static transcript analyzer — proves whether Claude followed §0 (runbook-first, no thrash).

Reads Claude Code JSONL transcripts from ~/.claude/projects/<project>/*.jsonl and
reports three anti-patterns for each session:

    A. runbook_missed   — lookup_runbook never called in a session that hit warn/fail
    B. runbook_late     — lookup_runbook called, but >3 MCP diagnostic tools ran before it
    C. thrash           — same MCP tool called 5+ times consecutively on the same target

Usage:
    runbook_compliance.py                        # summarise last 10 sessions
    runbook_compliance.py --ci                   # exit 1 if latest session hit any anti-pattern
    runbook_compliance.py --file <path>          # analyse a specific transcript
    runbook_compliance.py --project <dir-name>   # default: -Users-stephan-Documents-ops-agent

Emits JSON on stdout unless --pretty.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

DEFAULT_PROJECT = "-Users-stephan-Documents-ops-agent"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Tools whose output reveals warn/fail state that should trigger the §0 runbook-first rule.
TRIAGE_TRIGGER_TOOLS = {"mcp__ops__fleet_status", "mcp__ops__health_summary"}

# Diagnostic tools. Calling one of these before lookup_runbook (after a triage trigger) is "late".
DIAGNOSTIC_TOOLS = {
    "mcp__ops__tail_logs",
    "mcp__ops__read_file",
    "mcp__ops__list_containers",
    "mcp__ops__server_status",
    "mcp__ops__describe_server",
    "mcp__ops__wp_cli",
    "mcp__ops__hetzner_firewall",
    "mcp__ops__cloudflare_dns",
}

RUNBOOK_TOOL = "mcp__ops__lookup_runbook"

# Thrash: same tool + same primary target this many consecutive times.
THRASH_CONSECUTIVE = 5

# Tools to pull a "target" from (arg name -> priority).
TARGET_ARG_KEYS = ("container", "host", "path", "stack", "unit", "zone", "server")


@dataclass
class ToolCall:
    index: int
    name: str
    target: str | None


@dataclass
class SessionReport:
    session_id: str
    file: str
    first_prompt: str
    total_tool_calls: int
    mcp_ops_calls: int
    triage_triggered: bool
    runbook_called: bool
    runbook_call_position: int | None
    diagnostic_before_runbook: int
    thrash_runs: list[dict]
    anti_patterns: list[str]
    tool_sequence_head: list[str] = field(default_factory=list)

    def passed(self) -> bool:
        return not self.anti_patterns


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _primary_target(tool_name: str, tool_input: dict) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    for k in TARGET_ARG_KEYS:
        v = tool_input.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def _extract_tool_calls(events: Iterable[dict]) -> tuple[list[ToolCall], str]:
    calls: list[ToolCall] = []
    first_prompt = ""
    for ev in events:
        if not first_prompt and ev.get("type") == "user":
            msg = ev.get("message", {})
            content = msg.get("content")
            if isinstance(content, str):
                first_prompt = content.strip()[:240]
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        first_prompt = (block.get("text") or "").strip()[:240]
                        break
        if ev.get("type") != "assistant":
            continue
        content = ev.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name") or ""
                target = _primary_target(name, block.get("input") or {})
                calls.append(ToolCall(index=len(calls), name=name, target=target))
    return calls, first_prompt


def _find_thrash_runs(calls: list[ToolCall]) -> list[dict]:
    runs: list[dict] = []
    if not calls:
        return runs
    run_start = 0
    run_len = 1
    for i in range(1, len(calls)):
        same_tool = calls[i].name == calls[run_start].name
        same_target = calls[i].target == calls[run_start].target and calls[i].target is not None
        if same_tool and same_target:
            run_len += 1
        else:
            if run_len >= THRASH_CONSECUTIVE and calls[run_start].name.startswith("mcp__ops__"):
                runs.append({
                    "tool": calls[run_start].name,
                    "target": calls[run_start].target,
                    "consecutive": run_len,
                    "start_index": run_start,
                })
            run_start = i
            run_len = 1
    if run_len >= THRASH_CONSECUTIVE and calls[run_start].name.startswith("mcp__ops__"):
        runs.append({
            "tool": calls[run_start].name,
            "target": calls[run_start].target,
            "consecutive": run_len,
            "start_index": run_start,
        })
    return runs


def analyze(path: Path) -> SessionReport:
    calls, first_prompt = _extract_tool_calls(_iter_jsonl(path))
    mcp_ops_calls = sum(1 for c in calls if c.name.startswith("mcp__ops__"))

    triage_indexes = [c.index for c in calls if c.name in TRIAGE_TRIGGER_TOOLS]
    runbook_indexes = [c.index for c in calls if c.name == RUNBOOK_TOOL]
    triage_triggered = bool(triage_indexes)
    runbook_called = bool(runbook_indexes)
    runbook_call_position = runbook_indexes[0] if runbook_indexes else None

    # diagnostic_before_runbook: how many diagnostic MCP tools ran between the first triage trigger
    # and the first lookup_runbook (or end of session if runbook never called).
    diagnostic_before_runbook = 0
    if triage_triggered:
        start = triage_indexes[0] + 1
        end = runbook_call_position if runbook_called else len(calls)
        for c in calls[start:end]:
            if c.name in DIAGNOSTIC_TOOLS:
                diagnostic_before_runbook += 1

    thrash_runs = _find_thrash_runs(calls)

    anti_patterns: list[str] = []
    if triage_triggered and not runbook_called:
        anti_patterns.append("runbook_missed")
    elif triage_triggered and diagnostic_before_runbook > 3:
        anti_patterns.append("runbook_late")
    if thrash_runs:
        anti_patterns.append("thrash")

    return SessionReport(
        session_id=path.stem,
        file=str(path),
        first_prompt=first_prompt,
        total_tool_calls=len(calls),
        mcp_ops_calls=mcp_ops_calls,
        triage_triggered=triage_triggered,
        runbook_called=runbook_called,
        runbook_call_position=runbook_call_position,
        diagnostic_before_runbook=diagnostic_before_runbook,
        thrash_runs=thrash_runs,
        anti_patterns=anti_patterns,
        tool_sequence_head=[c.name.replace("mcp__ops__", "ops:") for c in calls[:20]],
    )


def _list_project_transcripts(project: str) -> list[Path]:
    d = PROJECTS_DIR / project
    if not d.is_dir():
        return []
    return sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=DEFAULT_PROJECT)
    ap.add_argument("--file", help="Analyse a single transcript file")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--ci", action="store_true", help="Exit non-zero if the latest session failed")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    if args.file:
        reports = [analyze(Path(args.file))]
    else:
        paths = _list_project_transcripts(args.project)[: args.limit]
        if not paths:
            print(json.dumps({"error": f"no transcripts found in {PROJECTS_DIR / args.project}"}))
            return 2
        reports = [analyze(p) for p in paths]

    aggregate = Counter()
    for r in reports:
        for ap_name in r.anti_patterns:
            aggregate[ap_name] += 1

    output = {
        "project": args.project,
        "sessions_analyzed": len(reports),
        "anti_pattern_counts": dict(aggregate),
        "sessions": [asdict(r) for r in reports],
    }

    if args.pretty:
        json.dump(output, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")

    if args.ci:
        # Latest (first) session must be clean.
        return 1 if reports and reports[0].anti_patterns else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
