"""Relay coordinator — bridges Supabase commands to the AI CLI adapter.

Listens for commands inserted into the `commands` table via Realtime,
executes them through the CLI adapter, and persists output chunks +
status updates back to Supabase.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from kaow.relay.subscription import RealtimeSubscription

if TYPE_CHECKING:
    from kaow.adapters.base import CLIAdapter
    from kaow.display.base import DisplayManager
    from kaow.relay.client import SupabaseClient

logger = logging.getLogger(__name__)

# Optional hook: async callback notified on each relay event (for bridging
# to local WebSocket clients). Receives the event name and a payload dict.
RelayHook = Callable[[str, dict[str, Any]], Awaitable[None]]


class RelayCoordinator:
    """Coordinates the Supabase relay for a single device.

    Handles device registration, realtime subscription, command
    execution, and persistence of outputs and screenshots.
    """

    def __init__(
        self,
        supabase: SupabaseClient,
        device_user_id: str,
        device_name: str,
        adapter: CLIAdapter,
        display: DisplayManager,
        hook: RelayHook | None = None,
    ) -> None:
        self._supabase = supabase
        self._device_user_id = device_user_id
        self._device_name = device_name
        self._adapter = adapter
        self._display = display
        self._hook = hook
        self._device_id: str | None = None
        self._subscription: RealtimeSubscription | None = None
        self._active_tasks: dict[str, asyncio.Task[None]] = {}

    @property
    def device_id(self) -> str | None:
        """Return the registered device UUID (None until started)."""
        return self._device_id

    @property
    def active_tasks(self) -> int:
        """Return the number of in-flight command tasks."""
        return len(self._active_tasks)

    def set_hook(self, hook: RelayHook | None) -> None:
        """Set or clear the event hook (e.g., for bridging to local clients)."""
        self._hook = hook

    async def start(self) -> None:
        """Connect, register the device, and subscribe to commands."""
        await self._supabase.connect()
        if not self._supabase.is_configured:
            raise RuntimeError("Supabase is not configured — cannot start relay")

        self._device_id = await self._supabase.register_device(
            user_id=self._device_user_id,
            device_name=self._device_name,
        )

        self._subscription = RealtimeSubscription(self._supabase, self._device_id)
        self._subscription.on_command(self._handle_command)
        await self._subscription.start()

        # Replay any commands queued while the daemon was offline.
        await self._replay_pending()
        logger.info("Relay started for device: %s", self._device_id)

    async def stop(self) -> None:
        """Cancel tasks and tear down Supabase connections."""
        for task in list(self._active_tasks.values()):
            task.cancel()
        for task in list(self._active_tasks.values()):
            with contextlib.suppress(asyncio.CancelledError):
                await task

        if self._subscription:
            await self._subscription.stop()
            self._subscription = None

        if self._device_id:
            await self._supabase.set_device_status(self._device_id, "offline")
        await self._supabase.disconnect()
        logger.info("Relay stopped")

    async def _replay_pending(self) -> None:
        """Execute commands that are still queued in Supabase."""
        assert self._device_id is not None
        pending = await self._supabase.get_pending_commands(self._device_id)
        for command in pending:
            command_id = str(command["id"])
            prompt = str(command["prompt"])
            logger.info("Replaying pending command: %s", command_id)
            await self._handle_command(command_id=command_id, prompt=prompt, device_id=self._device_id)

    async def _handle_command(self, command_id: str, prompt: str, device_id: str) -> None:
        """Execute a command from Supabase and persist results."""
        task = asyncio.create_task(self._run_command(command_id, prompt))
        self._active_tasks[command_id] = task
        task.add_done_callback(self._make_completion_callback(command_id))
        await self._notify("command_accepted", {"command_id": command_id, "prompt": prompt})

    def _make_completion_callback(self, command_id: str) -> Callable[[asyncio.Task[None]], None]:
        """Build a done-callback that removes a task from tracking."""
        def _done(task: asyncio.Task[None]) -> None:
            self._active_tasks.pop(command_id, None)

        return _done

    async def _run_command(self, command_id: str, prompt: str) -> None:
        """Run a command through the adapter, streaming to Supabase."""
        try:
            await self._supabase.update_command_status(command_id, "running")
            await self._notify("command_status", {"command_id": command_id, "status": "running"})

            seq = 0
            async for chunk in self._adapter.execute(prompt):
                await self._supabase.insert_command_output(command_id, chunk, seq)
                await self._notify("command_output", {"command_id": command_id, "chunk": chunk, "seq": seq})
                seq += 1

            await self._supabase.update_command_status(command_id, "completed")
            await self._notify("command_status", {"command_id": command_id, "status": "completed"})
        except asyncio.CancelledError:
            await self._supabase.update_command_status(command_id, "killed")
            await self._notify("command_status", {"command_id": command_id, "status": "killed"})
        except Exception as exc:
            logger.exception("Relay command failed: %s", command_id)
            await self._supabase.update_command_status(command_id, "failed", str(exc))
            await self._notify("command_status", {"command_id": command_id, "status": "failed"})

    async def _notify(self, event: str, payload: dict[str, Any]) -> None:
        """Notify the optional hook (e.g., to bridge to local WS clients)."""
        if self._hook:
            try:
                await self._hook(event, payload)
            except Exception:
                logger.exception("Relay hook failed for event: %s", event)
