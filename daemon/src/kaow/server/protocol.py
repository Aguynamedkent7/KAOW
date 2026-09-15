"""WebSocket message protocol — Pydantic models for all client-daemon messages."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

# --- Message Types ---


class MessageType(StrEnum):
    """All supported WebSocket message types."""

    # Client → Daemon
    COMMAND = "command"
    SCREENSHOT_REQUEST = "screenshot_request"
    KILL = "kill"
    PING = "ping"

    # Daemon → Client
    COMMAND_OUTPUT = "command_output"
    SCREENSHOT = "screenshot"
    ERROR = "error"
    PONG = "pong"
    TASK_QUEUED = "task_queued"
    STATUS = "status"


class TaskStatus(StrEnum):
    """Status of a running or completed task."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


# --- Client → Daemon Messages ---


class CommandPayload(BaseModel):
    """Payload for a command message sent from client to daemon."""

    prompt: str = Field(..., min_length=1, max_length=100_000, description="The prompt to send to the AI CLI")
    task_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique task identifier")


class KillPayload(BaseModel):
    """Payload for a kill message sent from client to daemon."""

    task_id: str = Field(..., description="ID of the task to terminate")


# --- Daemon → Client Messages ---


class CommandOutputPayload(BaseModel):
    """Streaming output from an AI CLI command execution."""

    task_id: str
    stream: str = Field(..., description="Output chunk or final result")
    done: bool = Field(default=False, description="Whether this is the final chunk")
    status: TaskStatus = Field(default=TaskStatus.RUNNING)


class ScreenshotPayload(BaseModel):
    """Screenshot data sent from daemon to client."""

    image: str = Field(..., description="Base64-encoded PNG screenshot")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    width: int = Field(default=1920)
    height: int = Field(default=1080)


class ErrorPayload(BaseModel):
    """Error message sent from daemon to client."""

    message: str
    code: str = Field(default="UNKNOWN_ERROR")
    task_id: str | None = None


class StatusPayload(BaseModel):
    """Daemon status report."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_tasks: int = 0
    display_active: bool = False
    cli_adapter: str = "unknown"


class TaskQueuedPayload(BaseModel):
    """Confirmation that a task was queued for later execution."""

    task_id: str
    queue_position: int


# --- Envelope ---


class WSMessage(BaseModel):
    """Universal WebSocket message envelope."""

    type: MessageType
    id: str = Field(default_factory=lambda: str(uuid4()), description="Message correlation ID")
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_json(self) -> str:
        """Serialize to JSON string for WebSocket transmission."""
        return self.model_dump_json()

    @classmethod
    def command(cls, payload: CommandPayload, msg_id: str | None = None) -> WSMessage:
        """Create a command message."""
        return cls(type=MessageType.COMMAND, id=msg_id or str(uuid4()), payload=payload.model_dump())

    @classmethod
    def command_output(cls, payload: CommandOutputPayload, msg_id: str | None = None) -> WSMessage:
        """Create a command output message."""
        return cls(type=MessageType.COMMAND_OUTPUT, id=msg_id or str(uuid4()), payload=payload.model_dump())

    @classmethod
    def screenshot(cls, payload: ScreenshotPayload, msg_id: str | None = None) -> WSMessage:
        """Create a screenshot message."""
        return cls(type=MessageType.SCREENSHOT, id=msg_id or str(uuid4()), payload=payload.model_dump())

    @classmethod
    def error(cls, payload: ErrorPayload, msg_id: str | None = None) -> WSMessage:
        """Create an error message."""
        return cls(type=MessageType.ERROR, id=msg_id or str(uuid4()), payload=payload.model_dump())

    @classmethod
    def status(cls, payload: StatusPayload, msg_id: str | None = None) -> WSMessage:
        """Create a status message."""
        return cls(type=MessageType.STATUS, id=msg_id or str(uuid4()), payload=payload.model_dump())

    @classmethod
    def task_queued(cls, payload: TaskQueuedPayload, msg_id: str | None = None) -> WSMessage:
        """Create a task queued confirmation."""
        return cls(type=MessageType.TASK_QUEUED, id=msg_id or str(uuid4()), payload=payload.model_dump())

    @classmethod
    def pong(cls, msg_id: str | None = None) -> WSMessage:
        """Create a pong response."""
        return cls(type=MessageType.PONG, id=msg_id or str(uuid4()))
