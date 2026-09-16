"""In-memory task queue — buffers commands when clients are disconnected."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QueuedTask:
    """A task waiting to be executed."""

    task_id: str
    prompt: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """Simple in-memory FIFO task queue.

    Buffers commands when no client is connected, replays them on reconnect.
    Command history is persisted locally in the SQLite transcript store.
    """

    def __init__(self, max_size: int = 100) -> None:
        self._queue: deque[QueuedTask] = deque(maxlen=max_size)
        self._max_size = max_size

    @property
    def size(self) -> int:
        """Return number of queued tasks."""
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Check if the queue has no pending tasks."""
        return len(self._queue) == 0

    def enqueue(self, task_id: str, prompt: str, **payload: Any) -> int:
        """Add a task to the queue.

        Args:
            task_id: Unique identifier for the task.
            prompt: The prompt to execute.
            **payload: Additional payload data.

        Returns:
            The position of the task in the queue (0-indexed).
        """
        if len(self._queue) >= self._max_size:
            logger.warning("Task queue full (max=%d), dropping oldest task", self._max_size)
            self._queue.popleft()

        task = QueuedTask(task_id=task_id, prompt=prompt, payload=payload)
        self._queue.append(task)
        position = len(self._queue) - 1
        logger.info("Task queued: %s (position %d)", task_id, position)
        return position

    def dequeue(self) -> QueuedTask | None:
        """Remove and return the oldest task from the queue.

        Returns:
            The next QueuedTask, or None if the queue is empty.
        """
        if self.is_empty:
            return None
        task = self._queue.popleft()
        logger.info("Task dequeued: %s", task.task_id)
        return task

    def peek(self) -> QueuedTask | None:
        """View the next task without removing it.

        Returns:
            The next QueuedTask, or None if the queue is empty.
        """
        return self._queue[0] if self._queue else None

    def cancel(self, task_id: str) -> bool:
        """Cancel a queued task by ID.

        Args:
            task_id: The task to remove from the queue.

        Returns:
            True if the task was found and removed.
        """
        for i, task in enumerate(self._queue):
            if task.task_id == task_id:
                del self._queue[i]
                logger.info("Task cancelled: %s", task_id)
                return True
        return False

    def clear(self) -> int:
        """Clear all queued tasks.

        Returns:
            Number of tasks that were cleared.
        """
        count = len(self._queue)
        self._queue.clear()
        logger.info("Queue cleared: %d tasks dropped", count)
        return count

    def drain(self) -> list[QueuedTask]:
        """Remove and return all queued tasks.

        Returns:
            List of all queued tasks in FIFO order.
        """
        tasks = list(self._queue)
        self._queue.clear()
        logger.info("Queue drained: %d tasks", len(tasks))
        return tasks
