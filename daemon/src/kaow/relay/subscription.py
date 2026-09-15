"""Realtime subscription handler — listens for commands via Supabase Realtime."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from realtime.types import PostgresChangesPayload, RealtimePostgresChangesListenEvent

if TYPE_CHECKING:
    from kaow.relay.client import SupabaseClient

logger = logging.getLogger(__name__)

# Callback type: async function that receives (command_id, prompt, device_id)
CommandCallback = Callable[[str, str, str], Awaitable[None]]


class RealtimeSubscription:
    """Manages Supabase Realtime subscriptions for a device.

    Subscribes to the `commands` table filtered by device_id.
    When a new command is inserted, invokes the callback.
    """

    def __init__(self, supabase: SupabaseClient, device_id: str) -> None:
        self._supabase = supabase
        self._device_id = device_id
        self._channel: Any = None
        self._callback: CommandCallback | None = None
        self._running = False
        self._pending_tasks: set[asyncio.Task[None]] = set()

    def on_command(self, callback: CommandCallback) -> None:
        """Register the callback to invoke when a new command arrives."""
        self._callback = callback

    async def start(self) -> None:
        """Subscribe to the commands table for this device."""
        if self._supabase.client is None:
            raise RuntimeError("SupabaseClient not connected")

        if self._running:
            logger.warning("Subscription already running")
            return

        self._running = True
        client = self._supabase.client

        # Subscribe to INSERT events on the commands table
        # Filter: device_id = this device
        self._channel = (
            client.realtime
            .channel("kaow:commands")
            .on_postgres_changes(
                event=RealtimePostgresChangesListenEvent.Insert,
                schema="public",
                table="commands",
                filter=f"device_id=eq.{self._device_id}",
                callback=self._on_insert,
            )
        )

        await self._channel.subscribe()
        logger.info(
            "Subscribed to commands for device: %s", self._device_id
        )

    async def stop(self) -> None:
        """Unsubscribe from the channel."""
        if self._channel and self._running:
            await self._channel.unsubscribe()
            self._running = False
            logger.info("Unsubscribed from commands channel")

    def _on_insert(self, payload: PostgresChangesPayload) -> None:
        """Handle a new command INSERT from Realtime.

        This is called from the realtime event loop, so we schedule
        the async callback on the main event loop.
        """
        data = payload.get("data")
        record = data.get("record") if data else None
        if not record:
            logger.warning("Realtime INSERT without record data — ignoring")
            return
        command_id = str(record.get("id", ""))
        prompt = str(record.get("prompt", ""))
        device_id = str(record.get("device_id", ""))

        logger.info("New command via Realtime: %s", command_id)

        if self._callback is None:
            logger.warning("No command callback registered — dropping command")
            return

        loop = asyncio.get_event_loop()
        task = loop.create_task(self._safe_callback(command_id, prompt, device_id))
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)

    async def _safe_callback(
        self, command_id: str, prompt: str, device_id: str
    ) -> None:
        """Invoke the callback with error handling."""
        try:
            assert self._callback is not None
            await self._callback(command_id, prompt, device_id)
        except Exception:
            logger.exception("Command callback failed: %s", command_id)
