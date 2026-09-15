"""Abstract base class for AI CLI adapters.

All adapters must implement execute() for streaming output and kill() for
task termination. Adapters are responsible for managing subprocess lifecycles.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Raised when an adapter encounters a fatal error."""


class CLIAdapter(ABC):
    """Abstract interface for wrapping AI CLI tools.

    Subclasses must implement:
    - execute(prompt): Stream CLI output chunks
    - kill(task_id): Terminate a running task
    - health_check(): Verify the CLI is available
    """

    @abstractmethod
    async def execute(self, prompt: str) -> AsyncGenerator[str, None]:
        """Execute a prompt through the AI CLI and stream output.

        Args:
            prompt: The user prompt to send to the AI CLI.

        Yields:
            Output chunks as they become available from the CLI.

        Raises:
            AdapterError: If the CLI fails to start or returns a fatal error.
        """
        yield ""  # pragma: no cover — must be overridden

    @abstractmethod
    async def kill(self, task_id: str) -> bool:
        """Terminate a running task.

        Args:
            task_id: The unique identifier of the task to kill.

        Returns:
            True if the task was successfully terminated, False otherwise.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the AI CLI is installed and accessible.

        Returns:
            True if the CLI is available and responsive.
        """
        ...  # pragma: no cover
