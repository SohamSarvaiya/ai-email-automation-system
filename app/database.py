"""SQLite storage: processed emails + activity log."""
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from app.schemas import ProcessedEmail

SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    sender TEXT, subject TEXT,
    category TEXT, method TEXT, confidence REAL,
    department TEXT, priority TEXT, needs_review INTEGER,
    result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL, event TEXT NOT NULL, email_id INTEGER, detail TEXT
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)  # new connection per call = thread safe
        conn.row_factory = sqlite3.Row
        return conn

    def save_email(self, p: ProcessedEmail) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO emails (created_at, sender, subject, category, method, confidence,"
                " department, priority, needs_review, result_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (p.received_at.isoformat(), p.email.sender, p.email.subject, p.final.category.value,
                 p.final.method, p.final.confidence, p.department, p.priority,
                 int(p.needs_human_review), p.model_dump_json()),
            )
            return cur.lastrowid

    def get_email(self, email_id: int) -> Optional[ProcessedEmail]:
        with self._conn() as c:
            row = c.execute("SELECT id, result_json FROM emails WHERE id=?", (email_id,)).fetchone()
        if not row:
            return None
        p = ProcessedEmail.model_validate_json(row["result_json"])
        p.id = row["id"]
        return p

    def list_emails(self, limit: int = 50, category: Optional[str] = None) -> list[dict]:
        q = ("SELECT id, created_at, sender, subject, category, method, confidence, department,"
             " priority, needs_review FROM emails")
        args: list = []
        if category:
            q += " WHERE category=?"
            args.append(category)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args).fetchall()]

    def log(self, event: str, email_id: Optional[int] = None, detail: str = "") -> None:
        with self._conn() as c:
            c.execute("INSERT INTO activity_log (ts, event, email_id, detail) VALUES (?,?,?,?)",
                      (datetime.now(timezone.utc).isoformat(), event, email_id, detail))

    def list_logs(self, limit: int = 100) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
