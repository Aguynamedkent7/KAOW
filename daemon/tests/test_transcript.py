"""Unit tests for the local SQLite transcript store."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kaow.transcript.sqlite import SqliteTranscriptStore

if TYPE_CHECKING:
    from pathlib import Path


def test_record_and_history(tmp_path: Path) -> None:
    """A recorded command with output appears in history."""
    store = SqliteTranscriptStore(str(tmp_path))
    store.record_command("t1", "hello world")
    store.append_output("t1", "chunk one", 0)
    store.append_output("t1", "chunk two", 1)
    store.update_status("t1", "completed", completed=True)

    history = store.history(limit=5)
    assert len(history) == 1
    assert history[0].prompt == "hello world"
    assert history[0].output == "chunk onechunk two"
    assert history[0].status == "completed"


def test_multiple_commands_ordered_by_created(tmp_path: Path) -> None:
    """History returns commands in chronological order."""
    store = SqliteTranscriptStore(str(tmp_path))
    store.record_command("first", "a")
    store.record_command("second", "b")
    history = store.history()
    assert [e.task_id for e in history] == ["first", "second"]


def test_duplicate_record_ignored(tmp_path: Path) -> None:
    """Inserting the same task_id twice does not error or create duplicates."""
    store = SqliteTranscriptStore(str(tmp_path))
    store.record_command("t1", "a")
    store.record_command("t1", "b")
    history = store.history()
    assert len(history) == 1
