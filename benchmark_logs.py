#!/usr/bin/env python3
"""
Log analysis benchmark: naive raw SSH vs MCP digest.

Task: Check all container logs on the main server for issues.

Approach A -- naive:
  Full vs-code system prompt + raw SSH log output from each container + prose response

Approach B -- MCP digest:
  Minimal ops-agent system prompt + tail_logs digest per container + JSON response
"""

import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

import anthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("Error: ANTHROPIC_API_KEY not set")
    sys.exit(1)

MODEL = "claude-haiku-4-5-20251001"
PRICE_IN  = 1.00  # per 1M tokens
PRICE_OUT = 5.00

# Containers to check on main server
CONTAINERS = [
    "traefik",
    "edumusik-net-wp",
    "edumusik-com-wp",
    "shared-mariadb-m04gs0sg0o4g4c4k480k0okc",
    "uptime-kuma",
]

client = anthropic.Anthropic(api_key=API_KEY)


def read_file(path: str) -> str:
    try:
        return Path(path).expanduser().read_text()
    except FileNotFoundError:
        return ""


# ── System prompts ────────────────────────────────────────────────────────────

GLOBAL_MD = read_file("~/.claude/CLAUDE.md")

FULL_DEV_SYSTEM = "\n\n".join([
    "# Global Rules", GLOBAL_MD,
    "# EduMusik Infrastructure Guide", read_file("~/Documents/vs-code/CLAUDE.md"),
])

OPS_AGENT_SYSTEM = "\n\n".join([
    "# Global Rules", GLOBAL_MD,
    "# ops-agent", read_file("~/Documents/ops-agent/CLAUDE.md"),
])


# ── Data collection ───────────────────────────────────────────────────────────

def ssh_main(cmd: str) -> str:
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
         "-i", os.environ.get("OPS_SSH_KEY", str(Path.home() / ".ssh/id_onyx_agent")),
         "stephan@192.168.50.3", cmd],
        capture_output=True, text=True, timeout=20
    )
    return (r.stdout + r.stderr).strip()


def get_raw_logs() -> str:
    """Raw tail of each container's logs -- what a naive dev session sends."""
    parts = []
    for container in CONTAINERS:
        raw = ssh_main(f"docker logs --tail 50 {container} 2>&1")
        parts.append(f"=== {container} (last 50 lines) ===\n{raw}")
    return "\n\n".join(parts)


def get_mcp_digests() -> list[dict]:
    """Call the MCP server's tail_logs logic locally for each container."""
    # Import the MCP server's digest logic directly
    sys.path.insert(0, str(Path.home() / "Documents/ops-agent/server"))

    # Inline digest -- mirrors tail_logs in server.py
    def digest(container: str) -> dict:
        raw = ssh_main(f"docker logs --tail 100 {container} 2>&1")
        ansi = re.compile(r'\x1b\[[0-9;]*m')
        raw_lines = [ansi.sub('', l) for l in raw.splitlines() if l.strip()]
        levels: dict = {"ERROR": [], "WARN": [], "INFO": [], "OTHER": []}
        ts_pat = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}')
        timestamps = []
        for line in raw_lines:
            m = ts_pat.search(line)
            if m:
                timestamps.append(m.group())
            upper = line.upper()
            if any(w in upper for w in ["ERROR", "EXCEPTION", "TRACEBACK"]):
                levels["ERROR"].append(line)
            elif "WARN" in upper:
                levels["WARN"].append(line)
            elif "INFO" in upper:
                levels["INFO"].append(line)
            else:
                levels["OTHER"].append(line)

        def _sig(line: str) -> str:
            line = ts_pat.sub('', line)
            line = re.sub(r'\d{1,3}(\.\d{1,3}){3}(:\d+)?', '<ip>', line)
            return re.sub(r'\s+', ' ', line).strip()

        seen: set = set()
        unique_info = []
        for line in reversed(levels["INFO"]):
            sig = _sig(line)
            if sig not in seen:
                seen.add(sig)
                unique_info.append(line)
            if len(unique_info) >= 3:
                break

        return {
            "container": container,
            "lines_analysed": len(raw_lines),
            "time_range": f"{timestamps[0]} → {timestamps[-1]}" if len(timestamps) >= 2 else "n/a",
            "levels": {k: len(v) for k, v in levels.items()},
            "errors": levels["ERROR"][:5],
            "warnings": levels["WARN"][:5],
            "sample_info": list(reversed(unique_info)),
        }

    return [digest(c) for c in CONTAINERS]


# ── API calls ─────────────────────────────────────────────────────────────────

def call_naive(raw_logs: str):
    t0 = time.monotonic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=FULL_DEV_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Check the main server logs for any issues that need attention.\n\n{raw_logs}"
        }],
    )
    return resp, round((time.monotonic() - t0) * 1000)


def call_mcp(digests: list[dict]):
    t0 = time.monotonic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=150,
        system=OPS_AGENT_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                "Log digests from main server containers (via MCP tail_logs):\n"
                + json.dumps(digests, indent=None)
                + '\n\nRespond ONLY with JSON: {"issues": [{"container": str, "severity": "error|warn|info", "summary": str}], "action_required": bool}'
            )
        }],
    )
    return resp, round((time.monotonic() - t0) * 1000)


# ── Report ────────────────────────────────────────────────────────────────────

def cost(in_tok, out_tok):
    return (in_tok * PRICE_IN + out_tok * PRICE_OUT) / 1_000_000

def monthly(c, interval_min=60):
    return c * (60 / interval_min) * 24 * 30

def hr():
    print("─" * 64)

def main():
    print(f"Containers: {', '.join(CONTAINERS)}")
    print()

    print("Collecting log data from main server…")
    t0 = time.monotonic()
    raw = get_raw_logs()
    raw_ms = round((time.monotonic() - t0) * 1000)

    t0 = time.monotonic()
    digests = get_mcp_digests()
    digest_ms = round((time.monotonic() - t0) * 1000)

    raw_chars = len(raw)
    digest_chars = len(json.dumps(digests))
    print(f"  Raw logs:    {raw_chars:,} chars ({raw_ms}ms)")
    print(f"  MCP digests: {digest_chars:,} chars ({digest_ms}ms)")
    print(f"  Input reduction: {round((1 - digest_chars/raw_chars)*100)}%")
    print()

    hr()
    print("APPROACH A -- naive (full dev context + raw logs + prose)")
    hr()
    resp_a, ms_a = call_naive(raw)
    in_a, out_a = resp_a.usage.input_tokens, resp_a.usage.output_tokens
    c_a = cost(in_a, out_a)
    print(f"  Input tokens:  {in_a:,}")
    print(f"  Output tokens: {out_a:,}")
    print(f"  Cost/call:     ${c_a:.6f}")
    print(f"  Monthly (1h):  ${monthly(c_a):.4f}")
    print(f"  Response preview:")
    for block in resp_a.content:
        if hasattr(block, "text"):
            print("  " + block.text[:300].replace("\n", "\n  "))

    hr()
    print("APPROACH B -- MCP digest (ops-agent context + digest + JSON)")
    hr()
    resp_b, ms_b = call_mcp(digests)
    in_b, out_b = resp_b.usage.input_tokens, resp_b.usage.output_tokens
    c_b = cost(in_b, out_b)
    print(f"  Input tokens:  {in_b:,}")
    print(f"  Output tokens: {out_b:,}")
    print(f"  Cost/call:     ${c_b:.6f}")
    print(f"  Monthly (1h):  ${monthly(c_b):.4f}")
    print(f"  Response:")
    for block in resp_b.content:
        if hasattr(block, "text"):
            print("  " + block.text.strip())

    hr()
    print("SAVINGS SUMMARY")
    hr()
    print(f"  Input:   {in_a:,} → {in_b:,}  ({round((1-in_b/in_a)*100)}% fewer)")
    print(f"  Output:  {out_a:,} → {out_b:,}  ({round((1-out_b/out_a)*100)}% fewer)")
    print(f"  Cost:    ${c_a:.6f} → ${c_b:.6f}  ({round((1-c_b/c_a)*100)}% cheaper)")
    print(f"  Monthly savings (1h cadence): ${monthly(c_a)-monthly(c_b):.4f}")


if __name__ == "__main__":
    main()
