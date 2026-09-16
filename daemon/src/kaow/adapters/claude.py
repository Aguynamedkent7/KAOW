"""Claude CLI adapter — wraps the Anthropic Claude CLI for headless execution."""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import TYPE_CHECKING

from kaow.adapters.base import AdapterError, CLIAdapter

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

DEFAULT_CLAUDE_PATH = "claude"


class ClaudeAdapter(CLIAdapter):
    """Adapter for the Anthropic Claude CLI.

    Spawns `claude` as a subprocess, pipes the prompt via stdin,
    and streams stdout/stderr back as output chunks.
    """

    def __init__(self, cli_path: str = DEFAULT_CLAUDE_PATH) -> None:
        self._cli_path = cli_path
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def execute(self, prompt: str) -> AsyncGenerator[str, None]:
        """Execute a prompt through the Claude CLI and stream output.

        Args:
            prompt: The prompt to send to Claude.

        Yields:
            Output chunks from the CLI subprocess.

        Raises:
            AdapterError: If the CLI binary is not found or fails to start.
        """
        if not shutil.which(self._cli_path):
            raise AdapterError(f"Claude CLI not found at: {self._cli_path}")

        task_id = str(id(prompt))  # Simple ID for tracking
        logger.info("Starting Claude CLI execution: %s", task_id)

        try:
            process = await asyncio.create_subprocess_exec(
                self._cli_path,
                "--print",
                "--output-format",
                "text",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._processes[task_id] = process

            stdout_data, stderr_data = await process.communicate(input=prompt.encode())

            if process.returncode != 0:
                error_output = stderr_data.decode(errors="replace").strip()
                raise AdapterError(
                    f"Claude CLI exited with code {process.returncode}: {error_output}"
                )

            output = stdout_data.decode(errors="replace")
            yield output

        except asyncio.CancelledError:
            logger.info("Claude CLI execution cancelled: %s", task_id)
            raise
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(f"Failed to execute Claude CLI: {exc}") from exc
        finally:
            self._processes.pop(task_id, None)
            logger.info("Claude CLI execution finished: %s", task_id)

    async def kill(self, task_id: str) -> bool:
        """Terminate a running Claude CLI process.

        Args:
            task_id: The task identifier (currently unused, kills all for safety).

        Returns:
            True if a process was terminated.
        """
        killed = False
        for pid, process in list(self._processes.items()):
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except TimeoutError:
                    process.kill()
                killed = True
                logger.info("Killed Claude process: %s", pid)
        return killed

    async def health_check(self) -> bool:
        """Verify the Claude CLI is installed and callable.

        Returns:
            True if the CLI binary exists and responds to --version.
        """
        if not shutil.which(self._cli_path):
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                self._cli_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=10.0)
            return process.returncode == 0
        except (TimeoutError, FileNotFoundError):
            return False
