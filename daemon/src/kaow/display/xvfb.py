"""Xvfb display manager — virtual framebuffer for Linux headless systems."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import signal

from kaow.display.base import DisplayError, DisplayManager
from kaow.display.screenshot import capture_x11_screenshot

logger = logging.getLogger(__name__)


class XvfbDisplay(DisplayManager):
    """Virtual display manager using Xvfb (X Virtual Framebuffer).

    Manages the lifecycle of an Xvfb process and provides screenshot
    capture from the virtual framebuffer.
    """

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        self._width = width
        self._height = height
        self._process: asyncio.subprocess.Process | None = None
        self._display_num: int = 99
        self._started = False

    @property
    def is_running(self) -> bool:
        """Check if Xvfb is currently running."""
        return self._started and self._process is not None and self._process.returncode is None

    @property
    def display_var(self) -> str:
        """Return the DISPLAY environment variable value."""
        return f":{self._display_num}"

    async def start(self) -> None:
        """Start the Xvfb virtual framebuffer.

        Finds an available display number and starts Xvfb with the configured
        resolution and color depth.

        Raises:
            DisplayError: If Xvfb binary is not found or fails to start.
        """
        if self.is_running:
            logger.warning("Xvfb is already running on %s", self.display_var)
            return

        if not shutil.which("Xvfb"):
            raise DisplayError("Xvfb binary not found. Install with: pacman -S xorg-server-xvfb")

        self._display_num = await self._find_available_display()
        display_addr = self.display_var

        cmd = [
            "Xvfb",
            display_addr,
            "-screen",
            "0",
            f"{self._width}x{self._height}x24",
            "-ac",
            "+extension",
            "GLX",
            "+render",
            "-noreset",
        ]

        logger.info("Starting Xvfb: %s", " ".join(cmd))

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise DisplayError(f"Failed to start Xvfb: {exc}") from exc

        await asyncio.sleep(0.5)

        if self._process.returncode is not None:
            stderr = await self._process.stderr.read()  # type: ignore[union-attr]
            raise DisplayError(
                f"Xvfb exited immediately with code {self._process.returncode}: "
                f"{stderr.decode(errors='replace')}"
            )

        os.environ["DISPLAY"] = display_addr
        self._started = True
        logger.info("Xvfb started on %s (%dx%d)", display_addr, self._width, self._height)

    async def stop(self) -> None:
        """Stop the Xvfb process and clean up."""
        if self._process is None:
            return

        logger.info("Stopping Xvfb on %s", self.display_var)
        try:
            self._process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()
        except ProcessLookupError:
            pass
        finally:
            self._process = None
            self._started = False
            if os.environ.get("DISPLAY") == self.display_var:
                os.environ.pop("DISPLAY", None)
            logger.info("Xvfb stopped")

    async def set_resolution(self, width: int, height: int) -> None:
        """Change resolution by restarting Xvfb with new dimensions.

        Args:
            width: New width in pixels.
            height: New height in pixels.

        Raises:
            DisplayError: If restart fails.
        """
        self._width = width
        self._height = height
        if self.is_running:
            await self.stop()
            await self.start()

    async def capture_screenshot(self) -> str:
        """Capture the current Xvfb framebuffer as base64 PNG.

        Returns:
            Base64-encoded PNG image string.

        Raises:
            DisplayError: If capture fails or display is not running.
        """
        if not self.is_running:
            raise DisplayError("Cannot capture screenshot: Xvfb is not running")

        return await capture_x11_screenshot(self.display_var, self._width, self._height)

    async def _find_available_display(self) -> int:
        """Find an available DISPLAY number starting from :99."""
        for num in range(99, 200):
            sock_path = f"/tmp/.X11-unix/X{num}"
            if not os.path.exists(sock_path):
                return num
        raise DisplayError("No available DISPLAY number found (99-199)")
