"""Telemetry collector — gathers system metrics and process health."""

from __future__ import annotations

import asyncio
import contextlib
import functools
import logging
import time
from typing import TYPE_CHECKING

import psutil

from kaow.telemetry.models import ProcessInfo, SystemMetrics, TelemetrySnapshot

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

TELEMETRY_INTERVAL = 5.0  # seconds between collections


class TelemetryCollector:
    """Collects and distributes system telemetry snapshots.

    Periodically gathers CPU, memory, disk, and process metrics,
    then distributes them to registered callbacks.
    """

    def __init__(self) -> None:
        self._callbacks: list[Callable[[TelemetrySnapshot], Awaitable[None]]] = []
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._pids_to_watch: set[int] = set()

    def register_callback(self, callback: Callable[[TelemetrySnapshot], Awaitable[None]]) -> None:
        """Register a callback to receive telemetry snapshots."""
        self._callbacks.append(callback)

    def watch_pid(self, pid: int) -> None:
        """Add a process PID to monitor."""
        self._pids_to_watch.add(pid)

    def unwatch_pid(self, pid: int) -> None:
        """Remove a process PID from monitoring."""
        self._pids_to_watch.discard(pid)

    async def start(self) -> None:
        """Start the periodic telemetry collection loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Telemetry collector started")

    async def stop(self) -> None:
        """Stop the telemetry collection loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Telemetry collector stopped")

    async def collect_once(self) -> TelemetrySnapshot:
        """Collect a single telemetry snapshot on demand."""
        return await self._collect_snapshot()

    async def _collection_loop(self) -> None:
        """Periodically collect and broadcast telemetry."""
        while self._running:
            try:
                snapshot = await self._collect_snapshot()
                for callback in self._callbacks:
                    try:
                        await callback(snapshot)
                    except Exception:
                        logger.exception("Telemetry callback failed")
                await asyncio.sleep(TELEMETRY_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Telemetry collection error")
                await asyncio.sleep(TELEMETRY_INTERVAL)

    async def _collect_snapshot(self) -> TelemetrySnapshot:
        """Gather all system metrics and process info."""
        system = await self._collect_system_metrics()
        processes = await self._collect_process_info()
        return TelemetrySnapshot(
            system=system,
            processes=processes,
            active_tasks=len(self._pids_to_watch),
        )

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Gather CPU, memory, disk, and uptime metrics."""
        loop = asyncio.get_event_loop()
        cpu_partial = functools.partial(psutil.cpu_percent, interval=0.1)
        cpu = await loop.run_in_executor(None, cpu_partial)
        mem = await loop.run_in_executor(None, psutil.virtual_memory)
        disk = await loop.run_in_executor(None, psutil.disk_usage, "/")
        boot_time = await loop.run_in_executor(None, psutil.boot_time)
        uptime = time.time() - boot_time

        return SystemMetrics(
            cpu_percent=cpu,
            memory_percent=mem.percent,
            memory_used_mb=mem.used / (1024 * 1024),
            memory_total_mb=mem.total / (1024 * 1024),
            disk_percent=disk.percent,
            uptime_seconds=uptime,
        )

    async def _collect_process_info(self) -> list[ProcessInfo]:
        """Gather info for watched processes."""
        infos: list[ProcessInfo] = []
        loop = asyncio.get_event_loop()

        for pid in list(self._pids_to_watch):
            try:
                proc = await loop.run_in_executor(None, psutil.Process, pid)
                info = await loop.run_in_executor(None, self._get_process_info, proc)
                if info:
                    infos.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._pids_to_watch.discard(pid)

        return infos

    def _get_process_info(self, proc: psutil.Process) -> ProcessInfo | None:
        """Extract info from a psutil Process."""
        try:
            with proc.oneshot():
                return ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    status=proc.status(),
                    cpu_percent=proc.cpu_percent(),
                    memory_mb=proc.memory_info().rss / (1024 * 1024),
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
