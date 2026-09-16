"""KAOW WebSocket server — FastAPI application with WebSocket endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from kaow.server.middleware import AuthError, extract_token, validate_token
from kaow.server.protocol import (
    CommandOutputPayload,
    CommandPayload,
    ErrorPayload,
    HistoryEntry,
    HistoryPayload,
    HistoryResultPayload,
    KillPayload,
    MessageType,
    TaskStatus,
    WSMessage,
)

if TYPE_CHECKING:
    from kaow.adapters.base import CLIAdapter
    from kaow.display.base import DisplayManager
    from kaow.queue.memory import TaskQueue
    from kaow.telemetry.collector import TelemetryCollector
    from kaow.transcript.sqlite import SqliteTranscriptStore

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    @property
    def active_count(self) -> int:
        """Return number of active connections."""
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("Client connected. Total: %d", self.active_count)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("Client disconnected. Total: %d", self.active_count)

    async def broadcast(self, message: WSMessage) -> None:
        """Send a message to all connected clients."""
        data = message.to_json()
        disconnected: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(data)
            except Exception:
                logger.exception("Failed to send to client")
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


class KAOWServer:
    """Main KAOW daemon server — orchestrates adapters, display, telemetry."""

    def __init__(
        self,
        auth_token: str,
        adapter: CLIAdapter,
        display: DisplayManager,
        telemetry: TelemetryCollector,
        task_queue: TaskQueue,
        transcript: SqliteTranscriptStore,
    ) -> None:
        self._auth_token = auth_token
        self._adapter = adapter
        self._display = display
        self._telemetry = telemetry
        self._task_queue = task_queue
        self._transcript = transcript
        self._connections = ConnectionManager()
        self._active_tasks: dict[str, asyncio.Task[None]] = {}

    @property
    def app(self) -> FastAPI:
        """Build and return the FastAPI application."""
        application = FastAPI(title="KAOW Daemon", version="0.1.0")
        application.add_api_websocket_route("/ws", self._handle_ws)
        return application

    async def _handle_ws(self, websocket: WebSocket) -> None:
        """Handle a single WebSocket connection lifecycle."""
        try:
            token = extract_token(websocket)
            validate_token(token, self._auth_token)
        except AuthError as exc:
            await websocket.accept()
            error_msg = WSMessage.error(ErrorPayload(message=exc.message, code="AUTH_FAILED"))
            await websocket.send_text(error_msg.to_json())
            await websocket.close(code=4001, reason="Authentication failed")
            return

        await self._connections.connect(websocket)
        try:
            await self._connection_loop(websocket)
        except WebSocketDisconnect:
            logger.info("Client disconnected normally")
        except Exception:
            logger.exception("Unexpected error in WebSocket handler")
        finally:
            self._connections.disconnect(websocket)

    async def _connection_loop(self, websocket: WebSocket) -> None:
        """Process messages from a connected client."""
        while True:
            raw = await websocket.receive_text()
            try:
                msg_data = json.loads(raw)
            except json.JSONDecodeError as exc:
                error = WSMessage.error(
                    ErrorPayload(message=f"Invalid JSON: {exc}", code="INVALID_MESSAGE")
                )
                await websocket.send_text(error.to_json())
                continue

            if not isinstance(msg_data, dict) or "type" not in msg_data:
                error = WSMessage.error(
                    ErrorPayload(
                        message="Message must be an object with a 'type' field",
                        code="INVALID_MESSAGE",
                    )
                )
                await websocket.send_text(error.to_json())
                continue

            try:
                msg_type = MessageType(msg_data["type"])
            except ValueError:
                error = WSMessage.error(
                    ErrorPayload(
                        message=f"Unknown message type: {msg_data['type']}", code="UNKNOWN_TYPE"
                    )
                )
                await websocket.send_text(error.to_json())
                continue

            msg_id = msg_data.get("id", "")
            payload = msg_data.get("payload", {})
            if not isinstance(payload, dict):
                error = WSMessage.error(
                    ErrorPayload(message="'payload' must be an object", code="INVALID_MESSAGE")
                )
                await websocket.send_text(error.to_json())
                continue

            if msg_type == MessageType.COMMAND:
                await self._handle_command(payload, msg_id)
            elif msg_type == MessageType.SCREENSHOT_REQUEST:
                await self._handle_screenshot(msg_id)
            elif msg_type == MessageType.KILL:
                await self._handle_kill(payload)
            elif msg_type == MessageType.HISTORY:
                await self._handle_history(payload, msg_id, websocket)
            elif msg_type == MessageType.PING:
                await websocket.send_text(WSMessage.pong(msg_id).to_json())
            else:
                error = WSMessage.error(
                    ErrorPayload(
                        message=f"Unhandled message type: {msg_type}", code="UNKNOWN_TYPE"
                    ),
                    msg_id=msg_id,
                )
                await websocket.send_text(error.to_json())

    async def _handle_command(self, payload: dict[str, Any], msg_id: str) -> None:
        """Dispatch an AI CLI command and stream output back to clients."""
        try:
            cmd = CommandPayload(**payload)
        except Exception as exc:
            error = WSMessage.error(
                ErrorPayload(message=f"Invalid command payload: {exc}", code="INVALID_PAYLOAD"),
                msg_id=msg_id,
            )
            await self._connections.broadcast(error)
            return

        try:
            await asyncio.to_thread(self._transcript.record_command, cmd.task_id, cmd.prompt)
        except Exception as exc:
            logger.exception("Failed to persist command: %s", cmd.task_id)
            error = WSMessage.error(
                ErrorPayload(
                    message=f"Failed to persist command: {exc}", code="PERSISTENCE_FAILED"
                ),
                msg_id=msg_id,
            )
            await self._connections.broadcast(error)

        task = asyncio.create_task(self._run_command(cmd, msg_id))
        self._active_tasks[cmd.task_id] = task
        task.add_done_callback(lambda t: self._active_tasks.pop(cmd.task_id, None))

    async def _run_command(self, cmd: CommandPayload, msg_id: str) -> None:
        """Execute a command through the CLI adapter and stream output."""
        seq = 0
        try:
            output = WSMessage.command_output(
                CommandOutputPayload(
                    task_id=cmd.task_id, stream="", done=False, status=TaskStatus.RUNNING
                ),
                msg_id=msg_id,
            )
            await self._connections.broadcast(output)

            async for chunk in self._adapter.execute(cmd.prompt):
                try:
                    await asyncio.to_thread(self._transcript.append_output, cmd.task_id, chunk, seq)
                    seq += 1
                except Exception as exc:
                    logger.exception("Failed to persist output chunk: %s", cmd.task_id)
                    error = WSMessage.error(
                        ErrorPayload(
                            message=f"Failed to persist output: {exc}",
                            code="PERSISTENCE_FAILED",
                            task_id=cmd.task_id,
                        ),
                        msg_id=msg_id,
                    )
                    await self._connections.broadcast(error)
                output = WSMessage.command_output(
                    CommandOutputPayload(task_id=cmd.task_id, stream=chunk, done=False),
                    msg_id=msg_id,
                )
                await self._connections.broadcast(output)

            await asyncio.to_thread(
                self._transcript.update_status,
                cmd.task_id,
                TaskStatus.COMPLETED.value,
                completed=True,
            )
            done = WSMessage.command_output(
                CommandOutputPayload(
                    task_id=cmd.task_id, stream="", done=True, status=TaskStatus.COMPLETED
                ),
                msg_id=msg_id,
            )
            await self._connections.broadcast(done)
        except asyncio.CancelledError:
            await asyncio.to_thread(
                self._transcript.update_status,
                cmd.task_id,
                TaskStatus.KILLED.value,
                completed=True,
            )
            killed = WSMessage.command_output(
                CommandOutputPayload(
                    task_id=cmd.task_id, stream="Task killed", done=True, status=TaskStatus.KILLED
                ),
                msg_id=msg_id,
            )
            await self._connections.broadcast(killed)
        except Exception as exc:
            logger.exception("Command execution failed: %s", cmd.task_id)
            try:
                await asyncio.to_thread(
                    self._transcript.update_status,
                    cmd.task_id,
                    TaskStatus.FAILED.value,
                    completed=True,
                )
            except Exception:
                logger.exception("Failed to persist failure status: %s", cmd.task_id)
            error = WSMessage.error(
                ErrorPayload(message=str(exc), code="EXECUTION_FAILED", task_id=cmd.task_id),
                msg_id=msg_id,
            )
            await self._connections.broadcast(error)

    async def _handle_history(
        self, payload: dict[str, Any], msg_id: str, websocket: WebSocket
    ) -> None:
        """Return the local chat transcript to the requesting client."""
        try:
            request = HistoryPayload(**payload)
        except Exception as exc:
            error = WSMessage.error(
                ErrorPayload(message=f"Invalid history payload: {exc}", code="INVALID_PAYLOAD"),
                msg_id=msg_id,
            )
            await self._connections.broadcast(error)
            return

        entries = await asyncio.to_thread(self._transcript.history, request.limit)
        result = WSMessage.history_result(
            HistoryResultPayload(entries=[HistoryEntry(**entry.to_dict()) for entry in entries]),
            msg_id=msg_id,
        )
        await websocket.send_text(result.to_json())

    async def _handle_screenshot(self, msg_id: str) -> None:
        """Capture and broadcast a screenshot."""
        try:
            image_b64 = await self._display.capture_screenshot()
            from kaow.server.protocol import ScreenshotPayload

            msg = WSMessage.screenshot(ScreenshotPayload(image=image_b64), msg_id=msg_id)
            await self._connections.broadcast(msg)
        except Exception as exc:
            logger.exception("Screenshot capture failed")
            error = WSMessage.error(
                ErrorPayload(message=f"Screenshot failed: {exc}", code="SCREENSHOT_FAILED"),
                msg_id=msg_id,
            )
            await self._connections.broadcast(error)

    async def _handle_kill(self, payload: dict[str, Any]) -> None:
        """Kill a running task."""
        try:
            kill = KillPayload(**payload)
        except Exception as exc:
            error = WSMessage.error(
                ErrorPayload(message=f"Invalid kill payload: {exc}", code="INVALID_PAYLOAD")
            )
            await self._connections.broadcast(error)
            return

        task = self._active_tasks.get(kill.task_id)
        if task and not task.done():
            task.cancel()
            logger.info("Cancelled task: %s", kill.task_id)
        else:
            logger.warning("Task not found or already finished: %s", kill.task_id)
