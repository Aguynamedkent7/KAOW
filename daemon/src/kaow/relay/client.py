"""Supabase client wrapper — async client for DB + Realtime operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from supabase import AsyncClient, acreate_client

if TYPE_CHECKING:
    from kaow.config import Settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Async wrapper around the Supabase Python client.

    Provides typed helpers for the tables used by KAOW:
    devices, commands, command_outputs, screenshots.

    Uses the service_role key to bypass RLS (daemon runs server-side).
    """

    def __init__(self, settings: Settings) -> None:
        self._url = settings.supabase_url
        self._service_key = settings.supabase_service_key
        self._client: AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Check if Supabase credentials are provided."""
        return bool(self._url and self._service_key)

    @property
    def client(self) -> AsyncClient:
        """Return the underlying Supabase client.

        Raises RuntimeError if not yet initialised.
        """
        if self._client is None:
            raise RuntimeError("SupabaseClient not initialised. Call connect() first.")
        return self._client

    async def connect(self) -> None:
        """Create the async Supabase client."""
        if not self.is_configured:
            logger.warning("Supabase not configured — relay disabled")
            return
        self._client = await acreate_client(self._url, self._service_key)
        logger.info("Connected to Supabase: %s", self._url)

    async def disconnect(self) -> None:
        """Clean up the client connection."""
        self._client = None
        logger.info("Disconnected from Supabase")

    # ------------------------------------------------------------------
    # Device operations
    # ------------------------------------------------------------------

    async def register_device(
        self,
        user_id: str,
        device_name: str,
        public_key: str | None = None,
    ) -> str:
        """Register (upsert) this device with Supabase. Returns device UUID."""
        result = await self.client.rpc(
            "register_device",
            {"p_user_id": user_id, "p_device_name": device_name, "p_public_key": public_key},
        ).execute()
        device_id = str(result.data)
        logger.info("Device registered: %s (user=%s)", device_id, user_id)
        return device_id

    async def set_device_status(self, device_id: str, status: str) -> None:
        """Update device status (online/offline/busy)."""
        await (
            self.client.table("devices")
            .update({"status": status, "last_seen": "now()"})
            .eq("id", device_id)
            .execute()
        )

    # ------------------------------------------------------------------
    # Command operations
    # ------------------------------------------------------------------

    async def update_command_status(
        self,
        command_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Update a command's status."""
        update: dict[str, Any] = {"status": status}
        if status == "running":
            update["started_at"] = "now()"
        elif status in ("completed", "failed", "killed"):
            update["completed_at"] = "now()"
        if error_message:
            update["error_message"] = error_message

        await (
            self.client.table("commands")
            .update(update)
            .eq("id", command_id)
            .execute()
        )

    async def insert_command_output(self, command_id: str, chunk: str, seq: int) -> None:
        """Insert a streaming output chunk."""
        await (
            self.client.table("command_outputs")
            .insert({"command_id": command_id, "chunk": chunk, "seq": seq})
            .execute()
        )

    # ------------------------------------------------------------------
    # Screenshot operations
    # ------------------------------------------------------------------

    async def insert_screenshot(
        self,
        device_id: str,
        image_base64: str,
        width: int,
        height: int,
        command_id: str | None = None,
    ) -> str:
        """Store a screenshot. Returns the screenshot UUID."""
        row: dict[str, Any] = {
            "device_id": device_id,
            "image_base64": image_base64,
            "width": width,
            "height": height,
        }
        if command_id:
            row["command_id"] = command_id

        result = (
            await self.client.table("screenshots")
            .insert(row)
            .execute()
        )
        rows: list[dict[str, Any]] = cast("list[dict[str, Any]]", result.data)
        return str(rows[0]["id"]) if rows else ""

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_pending_commands(self, device_id: str) -> list[dict[str, Any]]:
        """Fetch all queued commands for a device (used on reconnect)."""
        result = (
            await self.client.table("commands")
            .select("*")
            .eq("device_id", device_id)
            .eq("status", "queued")
            .order("created_at")
            .execute()
        )
        rows: list[dict[str, Any]] = cast("list[dict[str, Any]]", result.data)
        return rows
