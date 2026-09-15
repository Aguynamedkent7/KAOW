"""KAOW daemon entry point — initializes and runs the daemon server."""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import TYPE_CHECKING

from kaow.adapters.claude import ClaudeAdapter
from kaow.adapters.opendevin import OpenDevinAdapter
from kaow.config import CLIAdapterType, Settings, load_settings
from kaow.display.xvfb import XvfbDisplay
from kaow.queue.memory import TaskQueue
from kaow.server.app import KAOWServer
from kaow.telemetry.collector import TelemetryCollector

if TYPE_CHECKING:
    from collections.abc import Callable

    from kaow.adapters.base import CLIAdapter
    from kaow.display.base import DisplayManager


def create_adapter(settings: Settings) -> CLIAdapter:
    """Create the appropriate CLI adapter based on config."""
    adapters: dict[CLIAdapterType, Callable[[], CLIAdapter]] = {
        CLIAdapterType.CLAUDE: lambda: ClaudeAdapter(settings.cli_path),
        CLIAdapterType.OPENDEVIN: lambda: OpenDevinAdapter(settings.cli_path),
    }
    factory = adapters.get(settings.cli_adapter)
    if factory is None:
        raise ValueError(f"Unknown adapter type: {settings.cli_adapter}")
    return factory()


def create_display(settings: Settings) -> DisplayManager:
    """Create the display manager based on config."""
    return XvfbDisplay(
        width=settings.display_width,
        height=settings.display_height,
    )


def setup_logging(level: str) -> None:
    """Configure logging for the daemon."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


async def run_daemon(settings: Settings) -> None:
    """Run the KAOW daemon — start display, adapter, server, telemetry."""
    logger = logging.getLogger("kaow.main")

    adapter = create_adapter(settings)
    display = create_display(settings)
    telemetry = TelemetryCollector()
    task_queue = TaskQueue()

    server = KAOWServer(
        auth_token=settings.auth_token,
        adapter=adapter,
        display=display,
        telemetry=telemetry,
        task_queue=task_queue,
    )

    shutdown_event = asyncio.Event()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

    try:
        logger.info("Starting KAOW daemon...")
        logger.info("Adapter: %s (%s)", settings.cli_adapter, settings.cli_path)
        logger.info("Display: %s", settings.display_resolution)
        logger.info("Listening: ws://%s:%d/ws", settings.host, settings.port)

        await display.start()
        await telemetry.start()

        import uvicorn

        config = uvicorn.Config(
            app=server.app,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
        )
        uvicorn_server = uvicorn.Server(config)

        serve_task = asyncio.create_task(uvicorn_server.serve())
        logger.info("KAOW daemon started successfully")

        await shutdown_event.wait()

        logger.info("Shutting down KAOW daemon...")
        uvicorn_server.should_exit = True
        await serve_task
    except Exception:
        logger.exception("Fatal error in daemon")
        raise
    finally:
        await telemetry.stop()
        await display.stop()
        logger.info("KAOW daemon stopped")


def main() -> None:
    """Main entry point for the KAOW daemon."""
    settings = load_settings()
    setup_logging(settings.log_level)
    asyncio.run(run_daemon(settings))


if __name__ == "__main__":
    main()
