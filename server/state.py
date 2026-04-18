#!/usr/bin/env python3
"""Shared SQLite state for ops-mcp: audit log, server snapshots, runbook KB."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("OPS_STATE_DIR", str(Path.home() / ".ops-mcp"))) / "state.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                ts               TEXT NOT NULL,
                host             TEXT,
                tool             TEXT NOT NULL,
                args_json        TEXT,
                result_json      TEXT,
                duration_ms      INTEGER,
                allowed          INTEGER DEFAULT 1,
                verified_outcome TEXT,    -- 'success'|'failure'|null (null = read/non-mutation)
                pre_state        TEXT,    -- JSON snapshot before mutation
                post_state       TEXT,    -- JSON snapshot after mutation
                runbook_id       TEXT,    -- matched runbook entry id (if any)
                needs_review     INTEGER DEFAULT 0  -- 1 = surface in review queue
            );
            CREATE TABLE IF NOT EXISTS server_snapshots (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                data_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runbooks (
                id               TEXT PRIMARY KEY,  -- slug: tool-stack or tool-unit
                tool             TEXT NOT NULL,      -- compose_up|systemctl_restart|wp_cli
                target           TEXT NOT NULL,      -- stack/unit/container name
                problem_hint     TEXT,               -- optional: failure symptom that triggered it
                resolution_json  TEXT NOT NULL,      -- JSON: {args, expected_outcome}
                risk_level       TEXT DEFAULT 'runtime',  -- read|runtime|config
                success_count    INTEGER DEFAULT 0,
                failure_count    INTEGER DEFAULT 0,
                last_used        TEXT,
                created_date     TEXT NOT NULL,
                needs_review     INTEGER DEFAULT 0   -- 1 = pending human approval/update
            );
        """)
        # Migrate existing DBs: add new columns if missing
        existing = {r[1] for r in conn.execute("PRAGMA table_info(tool_calls)").fetchall()}
        for col, defn in [
            ("verified_outcome", "TEXT"),
            ("pre_state", "TEXT"),
            ("post_state", "TEXT"),
            ("runbook_id", "TEXT"),
            ("needs_review", "INTEGER DEFAULT 0"),
        ]:
            if col not in existing:
                conn.execute(f"ALTER TABLE tool_calls ADD COLUMN {col} {defn}")


def log_call(tool: str, args: dict, result, duration_ms: int = 0,
             allowed: bool = True, host: str = None,
             verified_outcome: str = None, pre_state=None, post_state=None,
             runbook_id: str = None, needs_review: bool = False):
    ts = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tool_calls "
            "(ts, host, tool, args_json, result_json, duration_ms, allowed,"
            " verified_outcome, pre_state, post_state, runbook_id, needs_review)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ts, host, tool,
                json.dumps(args),
                json.dumps(result if isinstance(result, (dict, list)) else str(result)),
                duration_ms,
                1 if allowed else 0,
                verified_outcome,
                json.dumps(pre_state) if pre_state is not None else None,
                json.dumps(post_state) if post_state is not None else None,
                runbook_id,
                1 if needs_review else 0,
            )
        )


def save_snapshot(data: dict):
    ts = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO server_snapshots (ts, data_json) VALUES (?,?)",
            (ts, json.dumps(data))
        )
        conn.execute(
            "DELETE FROM server_snapshots WHERE id NOT IN"
            " (SELECT id FROM server_snapshots ORDER BY id DESC LIMIT 100)"
        )


def recent_calls(limit: int = 50) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tool_calls ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def review_queue(limit: int = 20) -> list:
    """Return tool_calls and runbooks that need human review."""
    with _connect() as conn:
        calls = conn.execute(
            "SELECT * FROM tool_calls WHERE needs_review=1 ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        books = conn.execute(
            "SELECT * FROM runbooks WHERE needs_review=1 ORDER BY last_used DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return {
        "tool_calls": [dict(r) for r in calls],
        "runbooks": [dict(r) for r in books],
    }


def upsert_runbook(tool: str, target: str, resolution: dict,
                   risk_level: str = "runtime", problem_hint: str = None) -> str:
    """Create or return existing runbook entry. Returns runbook id."""
    rb_id = f"{tool}-{target}"
    ts = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        existing = conn.execute("SELECT id FROM runbooks WHERE id=?", (rb_id,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO runbooks (id, tool, target, problem_hint, resolution_json,"
                " risk_level, created_date, needs_review) VALUES (?,?,?,?,?,?,?,1)",
                (rb_id, tool, target, problem_hint, json.dumps(resolution), risk_level, ts)
            )
    return rb_id


def update_runbook_outcome(rb_id: str, success: bool):
    """Increment success or failure count for a runbook entry."""
    col = "success_count" if success else "failure_count"
    ts = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            f"UPDATE runbooks SET {col}={col}+1, last_used=?,"
            f" needs_review=CASE WHEN ? THEN 0 ELSE 1 END WHERE id=?",
            (ts, success, rb_id)
        )


def get_runbooks() -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM runbooks ORDER BY success_count DESC").fetchall()
    return [dict(r) for r in rows]


def latest_snapshot() -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM server_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None
