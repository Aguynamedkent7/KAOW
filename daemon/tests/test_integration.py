"""Integration tests — WebSocket server accepts connections and dispatches commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
from fastapi.testclient import TestClient

from kaow.adapters.base import CLIAdapter
from kaow.display.base import DisplayManager
from kaow.queue.memory import TaskQueue
from kaow.server.app import KAOWServer
from kaow.telemetry.collector import TelemetryCollector

AUTH_TOKEN = "integration-test-token"


class FakeAdapter(CLIAdapter):
    """Test adapter that yields deterministic output chunks."""

    async def execute(self, prompt: str) -> AsyncGenerator[str, None]:
        yield f"echo: {prompt}\n"

    async def kill(self, task_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


class FakeDisplay(DisplayManager):
    """Test display that returns fake screenshots."""

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


@pytest.fixture
def server() -> KAOWServer:
    """Create a KAOWServer with fake components."""
    return KAOWServer(
        auth_token=AUTH_TOKEN,
        adapter=FakeAdapter(),
        display=FakeDisplay(),
        telemetry=TelemetryCollector(),
        task_queue=TaskQueue(),
    )


@pytest.fixture
def client(server: KAOWServer) -> TestClient:
    """Create a TestClient against the server's FastAPI app."""
    return TestClient(server.app)


class TestAuthentication:
    """Tests for WebSocket authentication."""

    def test_missing_token_rejected(self, client: TestClient) -> None:
        """Connection without token is rejected with AUTH_FAILED."""
        with client.websocket_connect("/ws") as ws:
            response = ws.receive_json()
            assert response["type"] == "error"
            assert response["payload"]["code"] == "AUTH_FAILED"

    def test_invalid_token_rejected(self, client: TestClient) -> None:
        """Connection with wrong token is rejected."""
        with client.websocket_connect("/ws?token=wrong") as ws:
            response = ws.receive_json()
            assert response["type"] == "error"
            assert response["payload"]["code"] == "AUTH_FAILED"

    def test_valid_token_accepted(self, client: TestClient) -> None:
        """Connection with valid token is accepted (no immediate error)."""
        with client.websocket_connect(f"/ws?token={AUTH_TOKEN}") as ws:
            ws.send_json({"type": "ping", "payload": {}})
            response = ws.receive_json()
            assert response["type"] == "pong"


class TestCommandDispatch:
    """Tests for command execution through the WebSocket."""

    def test_command_streams_output(self, client: TestClient) -> None:
        """Command message produces streaming command_output messages.

        Expected flow: initial broadcast (running) → output chunk → done (completed).
        """
        with client.websocket_connect(f"/ws?token={AUTH_TOKEN}") as ws:
            ws.send_json(
                {
                    "type": "command",
                    "payload": {"prompt": "hello integration"},
                }
            )

            first = ws.receive_json()
            assert first["type"] == "command_output"
            assert first["payload"]["status"] == "running"
            assert first["payload"]["done"] is False

            chunk = ws.receive_json()
            assert chunk["type"] == "command_output"
            assert chunk["payload"]["stream"] == "echo: hello integration\n"
            assert chunk["payload"]["done"] is False

            final = ws.receive_json()
            assert final["type"] == "command_output"
            assert final["payload"]["done"] is True
            assert final["payload"]["status"] == "completed"

    def test_empty_command_rejected(self, client: TestClient) -> None:
        """Empty prompt produces an error message."""
        with client.websocket_connect(f"/ws?token={AUTH_TOKEN}") as ws:
            ws.send_json({"type": "command", "payload": {"prompt": ""}})

            response = ws.receive_json()
            assert response["type"] == "error"
            assert response["payload"]["code"] == "INVALID_PAYLOAD"

    def test_unknown_message_type(self, client: TestClient) -> None:
        """Unknown message type produces UNKNOWN_TYPE error."""
        with client.websocket_connect(f"/ws?token={AUTH_TOKEN}") as ws:
            ws.send_json({"type": "not_a_real_type", "payload": {}})

            response = ws.receive_json()
            assert response["type"] == "error"
            assert response["payload"]["code"] == "UNKNOWN_TYPE"


class TestScreenshot:
    """Tests for screenshot requests."""

    def test_screenshot_request_returns_image(self, client: TestClient) -> None:
        """Screenshot request returns base64 image payload."""
        with client.websocket_connect(f"/ws?token={AUTH_TOKEN}") as ws:
            ws.send_json({"type": "screenshot_request", "payload": {}})

            response = ws.receive_json()
            assert response["type"] == "screenshot"
            assert response["payload"]["image"] == "fake-base64-screenshot"
