"""Tests for Supabase relay — factory, coordinator, and subscription wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from kaow.config import RelayMode, Settings
from kaow.relay.client import SupabaseClient
from kaow.relay.coordinator import RelayCoordinator
from kaow.relay.factory import (
    create_relay,
    local_ws_enabled,
    relay_enabled,
    validate_relay_settings,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from kaow.adapters.base import CLIAdapter
from kaow.display.base import DisplayManager

DEVICE_USER_ID = "user-123"


class FakeAdapter(CLIAdapter):
    """Adapter that yields deterministic output chunks."""

    async def execute(self, prompt: str) -> AsyncGenerator[str, None]:
        yield f"echo: {prompt}\n"

    async def kill(self, task_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


class FakeDisplay(DisplayManager):
    """Display that returns fake screenshots."""

    _running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def set_resolution(self, width: int, height: int) -> None:
        pass

    async def capture_screenshot(self) -> str:
        return "fake-base64-screenshot"

    @property
    def is_running(self) -> bool:
        return self._running


class FakeSupabase(SupabaseClient):
    """In-memory Supabase client for relay tests."""

    def __init__(self) -> None:
        self.connected = False
        self.commands: dict[str, dict[str, object]] = {}
        self.outputs: list[dict[str, object]] = []
        self.device_id: str | None = None
        self.status_updates: list[tuple[str, str, str | None]] = []
        # Avoid touching the real client machinery.
        super().__init__(relay_settings())

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def client(self) -> object:  # type: ignore[override]
        return object()

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def register_device(
        self, user_id: str, device_name: str, public_key: str | None = None
    ) -> str:
        if self.device_id is None:
            self.device_id = "device-abc"
        return self.device_id

    async def set_device_status(self, device_id: str, status: str) -> None:
        pass

    async def update_command_status(
        self, command_id: str, status: str, error_message: str | None = None
    ) -> None:
        self.status_updates.append((command_id, status, error_message))

    async def insert_command_output(
        self, command_id: str, chunk: str, seq: int
    ) -> None:
        self.outputs.append({"command_id": command_id, "chunk": chunk, "seq": seq})

    async def insert_screenshot(
        self,
        device_id: str,
        image_base64: str,
        width: int,
        height: int,
        command_id: str | None = None,
    ) -> str:
        return "screenshot-1"

    async def get_pending_commands(self, device_id: str) -> list[dict[str, object]]:
        return []


def relay_settings() -> Settings:
    """Settings with Supabase + cloud relay configured (no secrets)."""
    return Settings(
        auth_token="test-token-12345",
        relay_mode=RelayMode.CLOUD,
        supabase_url="https://test.supabase.co",
        supabase_service_key="service-key",
        supabase_anon_key="anon-key",
        device_name="Test PC",
        device_user_id=DEVICE_USER_ID,
    )


class TestFactory:
    """Tests for relay factory helpers."""

    def test_relay_enabled(self) -> None:
        """Cloud and BOTH enable the relay; local does not."""
        assert not relay_enabled(RelayMode.LOCAL)
        assert relay_enabled(RelayMode.CLOUD)
        assert relay_enabled(RelayMode.BOTH)

    def test_local_ws_enabled(self) -> None:
        """Local and BOTH enable the WS server; cloud does not."""
        assert local_ws_enabled(RelayMode.LOCAL)
        assert not local_ws_enabled(RelayMode.CLOUD)
        assert local_ws_enabled(RelayMode.BOTH)

    def test_validate_relay_settings_missing_fields(self) -> None:
        """Incomplete cloud settings fail fast with ValueError."""
        settings = relay_settings()
        settings.supabase_url = ""
        with pytest.raises(ValueError, match="SUPABASE_URL"):
            validate_relay_settings(settings)

    def test_validate_relay_settings_ok(self) -> None:
        """Complete cloud settings pass validation."""
        validate_relay_settings(relay_settings())  # should not raise

    def test_create_relay_local_returns_none(self) -> None:
        """create_relay returns None for local mode."""
        settings = relay_settings()
        settings.relay_mode = RelayMode.LOCAL
        relay = create_relay(settings, FakeAdapter(), FakeDisplay())
        assert relay is None

    def test_create_relay_cloud_builds_coordinator(self) -> None:
        """create_relay builds a coordinator for cloud mode."""
        relay = create_relay(relay_settings(), FakeAdapter(), FakeDisplay())
        assert isinstance(relay, RelayCoordinator)

    def test_create_relay_cloud_missing_config_raises(self) -> None:
        """Unconfigured Supabase fails loudly (no silent fallback)."""
        settings = relay_settings()
        settings.supabase_service_key = ""
        with pytest.raises(ValueError, match="SUPABASE_SERVICE_KEY"):
            create_relay(settings, FakeAdapter(), FakeDisplay())


class TestCoordinator:
    """Tests for RelayCoordinator command handling."""

    @pytest.mark.asyncio
    async def test_handle_command_persists_output_and_status(self) -> None:
        """Running a command writes outputs and flips status to completed."""
        supabase = FakeSupabase()
        coordinator = RelayCoordinator(
            supabase=supabase,
            device_user_id=DEVICE_USER_ID,
            device_name="Test PC",
            adapter=FakeAdapter(),
            display=FakeDisplay(),
        )

        events: list[tuple[str, dict[str, object]]] = []

        async def hook(event: str, payload: dict[str, object]) -> None:
            events.append((event, payload))

        coordinator.set_hook(hook)

        await coordinator._handle_command("cmd-1", "hello relay", "device-abc")
        task = coordinator._active_tasks["cmd-1"]
        await task

        assert supabase.status_updates[0] == ("cmd-1", "running", None)
        assert supabase.status_updates[-1][1] == "completed"
        assert supabase.outputs[0]["chunk"] == "echo: hello relay\n"
        assert any(event == "command_accepted" for event, _ in events)
        assert any(event == "command_status" for event, _ in events)

    @pytest.mark.asyncio
    async def test_start_requires_configuration(self) -> None:
        """start() raises if Supabase is not configured."""
        settings = relay_settings()
        settings.supabase_url = ""
        coordinator = RelayCoordinator(
            supabase=SupabaseClient(settings),
            device_user_id=DEVICE_USER_ID,
            device_name="Test PC",
            adapter=FakeAdapter(),
            display=FakeDisplay(),
        )
        with pytest.raises(RuntimeError, match="not configured"):
            await coordinator.start()
