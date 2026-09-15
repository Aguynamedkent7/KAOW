"""Shared WebSocket protocol schemas — reference for client implementations.

This module mirrors the daemon's server/protocol.py models. The mobile app
should use equivalent Kotlin data classes for serialization.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """All supported WebSocket message types."""

    COMMAND = "command"
    SCREENSHOT_REQUEST = "screenshot_request"
    KILL = "kill"
    PING = "ping"
    COMMAND_OUTPUT = "command_output"
    SCREENSHOT = "screenshot"
    ERROR = "error"
    PONG = "pong"
    TASK_QUEUED = "task_queued"
    STATUS = "status"


class TaskStatus(str, Enum):
    """Status of a running or completed task."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


class WSMessage(BaseModel):
    """Universal WebSocket message envelope."""

    type: MessageType
    id: str = Field(default_factory=lambda: str(uuid4()))
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
