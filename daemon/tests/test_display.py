"""Tests for KAOW display managers."""

from __future__ import annotations

import os

import pytest

from kaow.config import CaptureMode
from kaow.display.base import DisplayManager
from kaow.display.xvfb import XvfbDisplay
from kaow.queue.memory import TaskQueue


class TestDisplayManagerBase:
    """Tests for the abstract DisplayManager interface."""

    def test_cannot_instantiate_abstract(self) -> None:
        """DisplayManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DisplayManager()  # type: ignore[abstract]


class TestXvfbDisplay:
    """Tests for the Xvfb display manager."""

    def test_init_defaults(self) -> None:
        """Default resolution is 1920x1080."""
        display = XvfbDisplay()
        assert display._width == 1920
        assert display._height == 1080
        assert display.is_running is False

    def test_init_custom_resolution(self) -> None:
        """Custom resolution is stored."""
        display = XvfbDisplay(width=1280, height=720)
        assert display._width == 1280
        assert display._height == 720

    def test_display_var(self) -> None:
        """Display variable returns correct format."""
        display = XvfbDisplay()
        assert display.display_var == ":99"

    def test_capture_mode_default(self) -> None:
        """Default capture mode is AUTO."""
        display = XvfbDisplay()
        assert display._capture_mode == CaptureMode.AUTO

    def test_capture_mode_custom(self) -> None:
        """Custom capture mode is stored."""
        display = XvfbDisplay(capture_mode=CaptureMode.VIRTUAL)
        assert display._capture_mode == CaptureMode.VIRTUAL

    def test_detect_real_display_no_env(self) -> None:
        """Detect returns None when DISPLAY is unset."""
        display = XvfbDisplay()
        with pytest.MonkeyPatch.context() as m:
            m.delenv("DISPLAY", raising=False)
            result = display._detect_real_display()
        assert result is None

    def test_detect_real_display_same_as_virtual(self) -> None:
        """Detect ignores DISPLAY if it matches our virtual display."""
        display = XvfbDisplay()
        with pytest.MonkeyPatch.context() as m:
            m.setenv("DISPLAY", display.display_var)
            result = display._detect_real_display()
        assert result is None

    def test_detect_real_display_valid(self) -> None:
        """Detect returns DISPLAY when a real X11 socket is present."""
        display = XvfbDisplay()
        with pytest.MonkeyPatch.context() as m:
            m.setenv("DISPLAY", ":0")
            real_exists = os.path.exists

            def fake_exists(path: str) -> bool:
                if path == "/tmp/.X11-unix/X0":
                    return True
                return real_exists(path)

            m.setattr(os.path, "exists", fake_exists)
            result = display._detect_real_display()
        assert result == ":0"

    def test_detect_real_display_wrong_number(self) -> None:
        """Detect ignores non-existent X11 sockets."""
        display = XvfbDisplay()
        with pytest.MonkeyPatch.context() as m:
            m.setenv("DISPLAY", ":42")
            result = display._detect_real_display()
        assert result is None


class TestTaskQueue:
    """Tests for the in-memory task queue."""

    def test_enqueue_returns_position(self) -> None:
        """Enqueue returns the queue position."""
        queue = TaskQueue()
        pos = queue.enqueue("t-1", "prompt 1")
        assert pos == 0

    def test_fifo_order(self) -> None:
        """Tasks are dequeued in FIFO order."""
        queue = TaskQueue()
        queue.enqueue("t-1", "first")
        queue.enqueue("t-2", "second")
        queue.enqueue("t-3", "third")

        t1 = queue.dequeue()
        t2 = queue.dequeue()
        t3 = queue.dequeue()

        assert t1 is not None and t1.task_id == "t-1"
        assert t2 is not None and t2.task_id == "t-2"
        assert t3 is not None and t3.task_id == "t-3"

    def test_dequeue_empty(self) -> None:
        """Dequeue from empty queue returns None."""
        queue = TaskQueue()
        assert queue.dequeue() is None

    def test_cancel_task(self) -> None:
        """Cancel removes a task from the queue."""
        queue = TaskQueue()
        queue.enqueue("t-1", "prompt 1")
        queue.enqueue("t-2", "prompt 2")

        result = queue.cancel("t-1")
        assert result is True
        assert queue.size == 1

    def test_cancel_nonexistent(self) -> None:
        """Cancel returns False for unknown task ID."""
        queue = TaskQueue()
        result = queue.cancel("nonexistent")
        assert result is False

    def test_max_size_eviction(self) -> None:
        """Queue evicts oldest task when full."""
        queue = TaskQueue(max_size=2)
        queue.enqueue("t-1", "first")
        queue.enqueue("t-2", "second")
        queue.enqueue("t-3", "third")

        assert queue.size == 2
        task = queue.dequeue()
        assert task is not None and task.task_id == "t-2"

    def test_clear(self) -> None:
        """Clear removes all tasks."""
        queue = TaskQueue()
        queue.enqueue("t-1", "a")
        queue.enqueue("t-2", "b")

        count = queue.clear()
        assert count == 2
        assert queue.is_empty

    def test_drain(self) -> None:
        """Drain returns all tasks and clears queue."""
        queue = TaskQueue()
        queue.enqueue("t-1", "a")
        queue.enqueue("t-2", "b")

        tasks = queue.drain()
        assert len(tasks) == 2
        assert queue.is_empty

    def test_peek(self) -> None:
        """Peek returns next task without removing it."""
        queue = TaskQueue()
        queue.enqueue("t-1", "a")
        queue.enqueue("t-2", "b")

        task = queue.peek()
        assert task is not None and task.task_id == "t-1"
        assert queue.size == 2
