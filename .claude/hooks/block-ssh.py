#!/usr/bin/env python3
"""Block direct SSH/server bash commands — force MCP tool use instead."""
import json
import sys

payload = json.load(sys.stdin)
cmd = payload.get("tool_input", {}).get("command", "")

SSH_PATTERNS = ["ssh ", "ssh\t", "docker ", "kubectl "]

if any(cmd.lstrip().startswith(p) for p in SSH_PATTERNS):
    print(json.dumps({
        "decision": "block",
        "reason": (
            "Direct SSH and Docker commands are disabled in ops-agent. "
            "Use the MCP tools instead: mcp__onyx-ops__server_status, "
            "mcp__onyx-ops__tail_logs, mcp__onyx-ops__list_containers, etc."
        )
    }))
    sys.exit(0)

# Allow everything else (local commands, python scripts, etc.)
print(json.dumps({"decision": "allow"}))
