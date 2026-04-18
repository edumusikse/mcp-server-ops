#!/usr/bin/env python3
"""Shared SQLite state for ops-mcp: audit log and server snapshots."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/home/stephan/.ops-mcp/state.db")


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          TEXT NOT NULL,
                tool        TEXT NOT NULL,
                args_json   TEXT,
                result_json TEXT,
                duration_ms INTEGER,
                allowed     INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS server_snapshots (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                data_json TEXT NOT NULL
            );
        """)


def log_call(tool: str, args: dict, result, duration_ms: int = 0, allowed: bool = True):
    ts = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tool_calls (ts, tool, args_json, result_json, duration_ms, allowed) VALUES (?,?,?,?,?,?)",
            (ts, tool, json.dumps(args), json.dumps(result if isinstance(result, (dict, list)) else str(result)),
             duration_ms, 1 if allowed else 0)
        )


def save_snapshot(data: dict):
    ts = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO server_snapshots (ts, data_json) VALUES (?,?)",
            (ts, json.dumps(data))
        )
        conn.execute(
            "DELETE FROM server_snapshots WHERE id NOT IN "
            "(SELECT id FROM server_snapshots ORDER BY id DESC LIMIT 100)"
        )


def recent_calls(limit: int = 50) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tool_calls ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def latest_snapshot() -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM server_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None
