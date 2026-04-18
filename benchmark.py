#!/usr/bin/env python3
"""
True overhead benchmark: ops-agent project vs full dev project.

Measures what actually loads into the system prompt for each project
and makes real Claude API calls to show the token cost difference.

Context A (full dev session — vs-code project):
  ~/.claude/CLAUDE.md  +  ~/Documents/vs-code/CLAUDE.md
  + skills (credentials, infrastructure, server-access, etc.)
  Estimated load: everything in those files per-message

Context B (ops-agent project):
  ~/.claude/CLAUDE.md  +  ~/Documents/ops-agent/CLAUDE.md
  No skills, no infrastructure docs

The question Claude answers in both contexts: "What is the server status?"
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import anthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("Error: ANTHROPIC_API_KEY environment variable not set")
    sys.exit(1)
MODEL = "claude-haiku-4-5-20251001"

PRICE_IN  = 1.00  # per 1M tokens
PRICE_OUT = 5.00

client = anthropic.Anthropic(api_key=API_KEY)


def read_file(path: str) -> str:
    try:
        return Path(path).expanduser().read_text()
    except FileNotFoundError:
        return ""


def count_tokens(text: str) -> int:
    """Estimate tokens via the API token-counting endpoint."""
    resp = client.messages.count_tokens(
        model=MODEL,
        system=text,
        messages=[{"role": "user", "content": "placeholder"}],
    )
    return resp.input_tokens


def ssh(cmd: str) -> str:
    r = subprocess.run(["ssh", "onyx", cmd], capture_output=True, text=True, timeout=15)
    return (r.stdout + r.stderr).strip()


# ── Build system prompts ──────────────────────────────────────────────────────

GLOBAL_CLAUDE_MD = read_file("~/.claude/CLAUDE.md")

# Approximate skill content that loads in a full dev session
# (just the SKILL.md files, not full content — they lazy-load)
SKILL_HEADERS = """
Skills available: credentials, infrastructure, server-access, bricks,
course-content, course-structure, auditing, content-writing.
Each skill has a SKILL.md and operational-learnings.md.
"""

FULL_DEV_SYSTEM = "\n\n".join([
    "# Global Rules",
    GLOBAL_CLAUDE_MD,
    "# EduMusik Infrastructure Guide",
    read_file("~/Documents/vs-code/CLAUDE.md"),
])

OPS_AGENT_SYSTEM = "\n\n".join([
    "# Global Rules",
    GLOBAL_CLAUDE_MD,
    "# ops-agent",
    read_file("~/Documents/ops-agent/CLAUDE.md"),
])

# ── Collect MCP digest (what ops-agent uses) ─────────────────────────────────

def get_mcp_digest() -> dict:
    """Simulate what mcp__onyx-ops__server_status returns."""
    ps_out = ssh("docker ps --format '{{.Names}}\\t{{.Status}}'")
    containers = []
    for line in ps_out.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            containers.append({"name": parts[0], "status": parts[1]})

    df_out = ssh("df -h / --output=pcent")
    disk_pct = df_out.splitlines()[-1].strip().rstrip("%") if df_out else "?"

    free_out = ssh("free -m")
    ram: dict = {}
    for line in free_out.splitlines():
        if line.startswith("Mem:"):
            p = line.split()
            if len(p) >= 3:
                total, used = int(p[1]), int(p[2])
                ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

    return {
        "containers": containers,
        "container_count": len(containers),
        "disk_pct": disk_pct,
        "ram": ram,
        "uptime": ssh("uptime -p"),
    }


def get_raw_status() -> str:
    """Raw SSH output — what a naive dev session produces."""
    fmt = "{{.Names}}\t{{.Status}}\t{{.RunningFor}}"
    ps = ssh(f"docker ps --format '{fmt}'")
    df = ssh("df -h /")
    fr = ssh("free -m")
    up = ssh("uptime")
    return f"=== docker ps ===\n{ps}\n\n=== df -h / ===\n{df}\n\n=== free -m ===\n{fr}\n\n=== uptime ===\n{up}"


# ── API calls ─────────────────────────────────────────────────────────────────

def call_full_dev(raw: str):
    """Full dev session: massive system prompt + raw output + prose response."""
    t0 = time.monotonic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=FULL_DEV_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"What is the server status?\n\n{raw}"
        }],
    )
    return resp, round((time.monotonic() - t0) * 1000)


def call_ops_agent(digest: dict):
    """ops-agent: minimal system prompt + MCP digest + structured JSON."""
    t0 = time.monotonic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=128,
        system=OPS_AGENT_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                "Server status (from MCP):\n"
                + json.dumps(digest)
                + '\n\nRespond ONLY with JSON: {"ok": bool, "alerts": [...], "action_required": bool}'
            )
        }],
    )
    return resp, round((time.monotonic() - t0) * 1000)


# ── Report ────────────────────────────────────────────────────────────────────

def cost(in_tok, out_tok):
    return (in_tok * PRICE_IN + out_tok * PRICE_OUT) / 1_000_000

def monthly(c, interval_min=5):
    return c * (60 / interval_min) * 24 * 30


def hr():
    print("─" * 62)


def main():
    print("Measuring system prompt sizes…")
    full_dev_sys_chars  = len(FULL_DEV_SYSTEM)
    ops_agent_sys_chars = len(OPS_AGENT_SYSTEM)
    print(f"  Full dev system prompt:  {full_dev_sys_chars:,} chars")
    print(f"  ops-agent system prompt: {ops_agent_sys_chars:,} chars")
    print(f"  Reduction:               {round((1 - ops_agent_sys_chars/full_dev_sys_chars)*100)}%")
    print()

    print("Collecting server data…")
    raw    = get_raw_status()
    digest = get_mcp_digest()
    print(f"  Raw input:    {len(raw):,} chars")
    print(f"  Digest input: {len(json.dumps(digest)):,} chars")
    print()

    hr()
    print("APPROACH A — full dev session (large context + raw SSH + prose)")
    hr()
    resp_a, ms_a = call_full_dev(raw)
    in_a  = resp_a.usage.input_tokens
    out_a = resp_a.usage.output_tokens
    c_a   = cost(in_a, out_a)
    print(f"  Input tokens:  {in_a:,}")
    print(f"  Output tokens: {out_a:,}")
    print(f"  Total tokens:  {in_a + out_a:,}")
    print(f"  Latency:       {ms_a} ms")
    print(f"  Cost/call:     ${c_a:.6f}")
    print(f"  Monthly:       ${monthly(c_a):.4f}")

    hr()
    print("APPROACH B — ops-agent (minimal context + MCP digest + JSON)")
    hr()
    resp_b, ms_b = call_ops_agent(digest)
    in_b  = resp_b.usage.input_tokens
    out_b = resp_b.usage.output_tokens
    c_b   = cost(in_b, out_b)
    print(f"  Input tokens:  {in_b:,}")
    print(f"  Output tokens: {out_b:,}")
    print(f"  Total tokens:  {in_b + out_b:,}")
    print(f"  Latency:       {ms_b} ms")
    print(f"  Cost/call:     ${c_b:.6f}")
    print(f"  Monthly:       ${monthly(c_b):.4f}")
    print()
    for block in resp_b.content:
        if hasattr(block, "text"):
            print("  Response:", block.text.strip())

    hr()
    print("SAVINGS SUMMARY")
    hr()
    total_a = in_a + out_a
    total_b = in_b + out_b
    print(f"  Input:   {in_a:,} → {in_b:,}  ({round((1-in_b/in_a)*100)}% fewer)")
    print(f"  Output:  {out_a:,} → {out_b:,}  ({round((1-out_b/out_a)*100)}% fewer)")
    print(f"  Total:   {total_a:,} → {total_b:,}  ({round((1-total_b/total_a)*100)}% fewer)")
    print(f"  Cost:    ${c_a:.6f} → ${c_b:.6f}  ({round((1-c_b/c_a)*100)}% cheaper)")
    print()
    m_a = monthly(c_a)
    m_b = monthly(c_b)
    print(f"  Monthly @ 5-min cadence:")
    print(f"    Full dev session: ${m_a:.4f}")
    print(f"    ops-agent:        ${m_b:.4f}")
    print(f"    Saving:           ${m_a-m_b:.4f}/month")


if __name__ == "__main__":
    main()
