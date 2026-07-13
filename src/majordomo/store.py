"""SQLite-backed memory store with full lifecycle provenance.

Every memory row keeps: who/when it came from (session, turn), how often it
was reinforced, and — when superseded — what replaced it and why. Nothing is
deleted; superseded memories stay queryable for audit, they just stop being
recalled. The store is deliberately plain SQL behind a small interface so the
Alibaba Cloud deployment can swap in ApsaraDB RDS without touching the engine.
"""

import json
import sqlite3
import time
from pathlib import Path

from majordomo.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id      TEXT NOT NULL,
    kind          TEXT NOT NULL DEFAULT 'preference',
    content       TEXT NOT NULL,
    embedding     TEXT NOT NULL,          -- JSON array
    importance    REAL NOT NULL DEFAULT 3,
    reinforcements INTEGER NOT NULL DEFAULT 1,
    created_at    REAL NOT NULL,
    last_seen_at  REAL NOT NULL,
    source_session TEXT NOT NULL,
    superseded_by INTEGER REFERENCES memories(id),
    supersede_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_mem_guest ON memories(guest_id, superseded_by);
"""


class MemoryStore:
    def __init__(self, db_path: Path | None = None):
        path = db_path or settings.db_path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)

    def add(self, guest_id: str, content: str, embedding: list[float],
            kind: str, importance: float, session_id: str) -> int:
        now = time.time()
        cur = self.con.execute(
            "INSERT INTO memories (guest_id, kind, content, embedding, importance,"
            " created_at, last_seen_at, source_session)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (guest_id, kind, content, json.dumps(embedding), importance, now, now, session_id),
        )
        self.con.commit()
        return cur.lastrowid

    def reinforce(self, memory_id: int) -> None:
        self.con.execute(
            "UPDATE memories SET reinforcements = reinforcements + 1, last_seen_at = ?"
            " WHERE id = ?", (time.time(), memory_id))
        self.con.commit()

    def supersede(self, old_id: int, new_id: int, reason: str) -> None:
        self.con.execute(
            "UPDATE memories SET superseded_by = ?, supersede_reason = ? WHERE id = ?",
            (new_id, reason, old_id))
        self.con.commit()

    def active(self, guest_id: str) -> list[dict]:
        rows = self.con.execute(
            "SELECT * FROM memories WHERE guest_id = ? AND superseded_by IS NULL",
            (guest_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["embedding"] = json.loads(d["embedding"])
            out.append(d)
        return out

    def history(self, guest_id: str) -> list[dict]:
        """Full audit trail including superseded rows (no embeddings)."""
        rows = self.con.execute(
            "SELECT id, kind, content, importance, reinforcements, source_session,"
            " superseded_by, supersede_reason FROM memories WHERE guest_id = ?"
            " ORDER BY id", (guest_id,)).fetchall()
        return [dict(r) for r in rows]

    def wipe(self) -> None:
        self.con.execute("DELETE FROM memories")
        self.con.commit()
