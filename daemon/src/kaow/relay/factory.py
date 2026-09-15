"""Relay factory — build RelayCoordinator and SupabaseClient from settings."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from kaow.config import RelayMode
from kaow.relay.client import SupabaseClient
from kaow.relay.coordinator import RelayCoordinator

if TYPE_CHECKING:
    from kaow.adapters.base import CLIAdapter
    from kaow.config import Settings
    from kaow.display.base import DisplayManager

logger = logging.getLogger(__name__)

RelayHook = Callable[[str, dict[str, Any]], Awaitable[None]]


def relay_enabled(mode: RelayMode) -> bool:
    """Return True if the relay should run for the given mode."""
    return mode in (RelayMode.CLOUD, RelayMode.BOTH)


def local_ws_enabled(mode: RelayMode) -> bool:
    """Return True if the local WebSocket server should run for the given mode."""
    return mode in (RelayMode.LOCAL, RelayMode.BOTH)


def validate_relay_settings(settings: Settings) -> None:
    """Fail loudly if cloud relay settings are incomplete.

    Raises:
        ValueError: If relay_mode is cloud/both but Supabase is unconfigured.
    """
    if not relay_enabled(settings.relay_mode):
        return
    missing = []
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_service_key:
        missing.append("SUPABASE_SERVICE_KEY")
    if not settings.device_user_id:
        missing.append("DEVICE_USER_ID")
    if missing:
        raise ValueError(
            f"Relay mode '{settings.relay_mode}' requires: {', '.join(missing)}. "
            "Set KAOW_SUPABASE_URL, KAOW_SUPABASE_SERVICE_KEY, and KAOW_DEVICE_USER_ID."
        )


def create_relay(
    settings: Settings,
    adapter: CLIAdapter,
    display: DisplayManager,
    hook: RelayHook | None = None,
) -> RelayCoordinator | None:
    """Build a RelayCoordinator if cloud relay is enabled.

    Args:
        settings: daemon settings.
        adapter: CLI adapter used to execute commands.
        display: display manager (reserved for screenshot persistence).
        hook: optional async (event, payload) callback served to local clients.

    Returns:
        RelayCoordinator, or None when relay_mode is local.
    """
    if not relay_enabled(settings.relay_mode):
        return None

    validate_relay_settings(settings)
    supabase = SupabaseClient(settings)
    return RelayCoordinator(
        supabase=supabase,
        device_user_id=settings.device_user_id,
        device_name=settings.device_name,
        adapter=adapter,
        display=display,
        hook=hook,
    )
