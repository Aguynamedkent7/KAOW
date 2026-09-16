"""Tests for KAOW WebSocket server and protocol."""

from __future__ import annotations

import json

import pytest

from kaow.server.protocol import (
    CommandOutputPayload,
    CommandPayload,
    ErrorPayload,
    MessageType,
    StatusPayload,
    TaskStatus,
    WSMessage,
)


class TestWSMessage:
    """Tests for the WSMessage envelope class."""

    def test_command_message(self) -> None:
        """Command message creates correct envelope."""
        payload = CommandPayload(prompt="hello world")
        msg = WSMessage.command(payload)
        assert msg.type == MessageType.COMMAND
        assert msg.payload["prompt"] == "hello world"
        assert "id" in msg.payload or msg.id

    def test_command_output_message(self) -> None:
        """Command output message includes task_id and done flag."""
        payload = CommandOutputPayload(task_id="task-1", stream="output text", done=False)
        msg = WSMessage.command_output(payload)
        assert msg.type == MessageType.COMMAND_OUTPUT
        assert msg.payload["task_id"] == "task-1"
        assert msg.payload["done"] is False

    def test_error_message(self) -> None:
        """Error message includes code and message."""
        payload = ErrorPayload(message="Something broke", code="TEST_ERROR")
        msg = WSMessage.error(payload)
        assert msg.type == MessageType.ERROR
        assert msg.payload["message"] == "Something broke"
        assert msg.payload["code"] == "TEST_ERROR"

    def test_pong_message(self) -> None:
        """Pong message has PONG type."""
        msg = WSMessage.pong(msg_id="ping-1")
        assert msg.type == MessageType.PONG

    def test_to_json_serialization(self) -> None:
        """to_json produces valid JSON with all fields."""
        payload = CommandPayload(prompt="test")
        msg = WSMessage.command(payload, msg_id="test-id")
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        assert parsed["type"] == "command"
        assert parsed["id"] == "test-id"
        assert "timestamp" in parsed

    def test_screenshot_message(self) -> None:
        """Screenshot message includes image data."""
        from kaow.server.protocol import ScreenshotPayload

        payload = ScreenshotPayload(image="base64data", width=1920, height=1080)
        msg = WSMessage.screenshot(payload)
        assert msg.type == MessageType.SCREENSHOT
        assert msg.payload["image"] == "base64data"

    def test_status_message(self) -> None:
        """Status message includes system metrics."""
        payload = StatusPayload(cpu_percent=45.2, memory_percent=67.8)
        msg = WSMessage.status(payload)
        assert msg.type == MessageType.STATUS
        assert msg.payload["cpu_percent"] == 45.2

    def test_task_queued_message(self) -> None:
        """Task queued message includes queue position."""
        from kaow.server.protocol import TaskQueuedPayload

        payload = TaskQueuedPayload(task_id="t-1", queue_position=3)
        msg = WSMessage.task_queued(payload)
        assert msg.type == MessageType.TASK_QUEUED
        assert msg.payload["queue_position"] == 3


class TestCommandPayload:
    """Tests for CommandPayload validation."""

    def test_valid_payload(self) -> None:
        """Valid prompt is accepted."""
        payload = CommandPayload(prompt="do something")
        assert payload.prompt == "do something"
        assert payload.task_id  # auto-generated

    def test_empty_prompt_rejected(self) -> None:
        """Empty prompt raises validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CommandPayload(prompt="")


class TestMessageType:
    """Tests for MessageType enum."""

    def test_client_to_daemon_types(self) -> None:
        """All client-to-daemon message types are defined."""
        assert MessageType.COMMAND.value == "command"
        assert MessageType.SCREENSHOT_REQUEST.value == "screenshot_request"
        assert MessageType.KILL.value == "kill"
        assert MessageType.PING.value == "ping"

    def test_daemon_to_client_types(self) -> None:
        """All daemon-to-client message types are defined."""
        assert MessageType.COMMAND_OUTPUT.value == "command_output"
        assert MessageType.SCREENSHOT.value == "screenshot"
        assert MessageType.ERROR.value == "error"
        assert MessageType.PONG.value == "pong"


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_all_statuses(self) -> None:
        """All task statuses are defined."""
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.KILLED.value == "killed"
