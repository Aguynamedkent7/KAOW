"""Telemetry data models — Pydantic schemas for system health metrics."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    """System resource usage snapshot."""

    cpu_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_used_mb: float = Field(default=0.0, ge=0.0)
    memory_total_mb: float = Field(default=0.0, ge=0.0)
    disk_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    uptime_seconds: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProcessInfo(BaseModel):
    """Information about a tracked process."""

    pid: int
    name: str
    status: str  # running, sleeping, stopped, zombie
    cpu_percent: float = 0.0
    memory_mb: float = 0.0


class TelemetrySnapshot(BaseModel):
    """Complete telemetry snapshot combining system and process data."""

    system: SystemMetrics
    processes: list[ProcessInfo] = Field(default_factory=list)
    active_tasks: int = 0
    display_active: bool = False
    cli_adapter: str = "unknown"
