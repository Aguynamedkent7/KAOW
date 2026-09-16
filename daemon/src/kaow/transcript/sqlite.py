"""Local transcript persistence backed by SQLite - user data stays on the PC."""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class TranscriptEntry:
    """A completed/existing command with its accumulated output text."""

    def __init__(
        self,
        task_id: str,
        prompt: str,
        status: str,
        created_at: str,
        output: str = "",
    ) -> None:
        self.task_id = task_id
        self.prompt = prompt
        self.status = status
        self.created_at = created_at
        self.output = output

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the WebSocket protocol."""
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "status": self.status,
            "created_at": self.created_at,
            "output": self.output,
        }


class SqliteTranscriptStore:
    """Append-only transcript store using a thread-local sqlite3 connection."""

    def __init__(self, data_dir: str) -> None:
        Path(os.path.expanduser(data_dir)).mkdir(parents=True, exist_ok=True)
        self._db_path = Path(os.path.expanduser(data_dir)) / "transcript.db"
        self._local = threading.local()
        self._init_schema()

    @property
    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode = WAL")
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id    TEXT PRIMARY KEY,
                prompt     TEXT NOT NULL,
                status     TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS outputs (
                task_id    TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                seq        INTEGER NOT NULL,
                chunk      TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (task_id, seq)
            );
            """
        )
        self._conn.commit()

    def record_command(self, task_id: str, prompt: str, status: str = "queued") -> None:
        """Insert a new command row (ignores duplicates)."""
        created = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT OR IGNORE INTO tasks (task_id, prompt, status, created_at) VALUES (?, ?, ?, ?)",
            (task_id, prompt, status, created),
        )
        self._conn.commit()

    def append_output(self, task_id: str, chunk: str, seq: int) -> None:
        """Append one streaming output chunk."""
        self._conn.execute(
            "INSERT OR IGNORE INTO outputs (task_id, seq, chunk, created_at) VALUES (?, ?, ?, ?)",
            (task_id, seq, chunk, datetime.now(UTC).isoformat()),
        )
        self._conn.commit()

    def update_status(self, task_id: str, status: str, completed: bool = False) -> None:
        """Update a command's status; optionally stamp completion time."""
        completed_at = datetime.now(UTC).isoformat() if completed else None
        self._conn.execute(
            "UPDATE tasks SET status = ?, completed_at = COALESCE(completed_at, ?) "
            "WHERE task_id = ?",
            (status, completed_at, task_id),
        )
        self._conn.commit()

    def history(self, limit: int = 50) -> list[TranscriptEntry]:
        """Return the most recent commands with their accumulated output."""
        rows = self._conn.execute(
            "SELECT task_id, prompt, status, created_at FROM tasks ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        entries: list[TranscriptEntry] = []
        for task_id, prompt, status, created_at in rows:
            out = self._conn.execute(
                "SELECT chunk FROM outputs WHERE task_id = ? ORDER BY seq ASC",
                (task_id,),
            ).fetchall()
            entries.append(
                TranscriptEntry(
                    task_id=task_id,
                    prompt=prompt,
                    status=status,
                    created_at=created_at,
                    output="".join(r[0] for r in out),
                )
            )
        return list(reversed(entries))

    def close(self) -> None:
        """Close the thread-local connection if open."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
