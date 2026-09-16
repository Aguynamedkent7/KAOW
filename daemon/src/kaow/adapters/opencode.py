"""OpenCode adapter — wraps the opencode CLI for headless execution."""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import TYPE_CHECKING

from kaow.adapters.base import AdapterError, CLIAdapter

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

DEFAULT_OPENCODE_PATH = "opencode"


class OpenCodeAdapter(CLIAdapter):
    """Adapter for the opencode CLI.

    Spawns `opencode run "<prompt>"` as a subprocess and streams output chunks.
    """

    def __init__(self, cli_path: str = DEFAULT_OPENCODE_PATH) -> None:
        self._cli_path = cli_path
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def execute(self, prompt: str) -> AsyncGenerator[str, None]:
        """Execute a prompt through the opencode CLI and stream output.

        Args:
            prompt: The task description to send to opencode.

        Yields:
            Output chunks from the CLI subprocess.

        Raises:
            AdapterError: If the CLI binary is not found or fails to start.
        """
        if not shutil.which(self._cli_path):
            raise AdapterError(f"opencode CLI not found at: {self._cli_path}")

        task_id = str(id(prompt))
        logger.info("Starting opencode CLI execution: %s", task_id)

        try:
            process = await asyncio.create_subprocess_exec(
                self._cli_path,
                "run",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._processes[task_id] = process

            async for line in process.stdout:  # type: ignore[union-attr]
                yield line.decode(errors="replace")

            await process.wait()

            if process.returncode != 0:
                stderr_data = await process.stderr.read()  # type: ignore[union-attr]
                error_output = stderr_data.decode(errors="replace").strip()
                raise AdapterError(
                    f"opencode CLI exited with code {process.returncode}: {error_output}"
                )

        except asyncio.CancelledError:
            logger.info("opencode CLI execution cancelled: %s", task_id)
            raise
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(f"Failed to execute opencode CLI: {exc}") from exc
        finally:
            self._processes.pop(task_id, None)
            logger.info("opencode CLI execution finished: %s", task_id)

    async def kill(self, task_id: str) -> bool:
        """Terminate running opencode processes.

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
                logger.info("Killed opencode process: %s", pid)
        return killed

    async def health_check(self) -> bool:
        """Verify the opencode CLI is installed and callable.

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
