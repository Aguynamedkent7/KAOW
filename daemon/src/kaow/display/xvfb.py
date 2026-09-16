"""Xvfb display manager — virtual framebuffer for Linux headless systems."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import signal

from kaow.config import CaptureMode
from kaow.display.base import DisplayError, DisplayManager
from kaow.display.screenshot import capture_screenshot, capture_x11_screenshot

logger = logging.getLogger(__name__)


class XvfbDisplay(DisplayManager):
    """Virtual display manager using Xvfb (X Virtual Framebuffer).

    Manages the lifecycle of an Xvfb process and provides screenshot
    capture. In AUTO mode, screenshots come from the user's real display
    when one is visible, falling back to the virtual framebuffer.
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        capture_mode: CaptureMode = CaptureMode.AUTO,
    ) -> None:
        self._width = width
        self._height = height
        self._capture_mode = capture_mode
        self._process: asyncio.subprocess.Process | None = None
        self._display_num: int = 99
        self._started = False
        self._real_display: str | None = None

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

        self._real_display = self._detect_real_display()
        os.environ["DISPLAY"] = display_addr
        self._started = True
        logger.info("Xvfb started on %s (%dx%d)", display_addr, self._width, self._height)
        if self._real_display is not None:
            logger.info("Real display detected for capture fallback: %s", self._real_display)

    def _detect_real_display(self) -> str | None:
        """Detect a live, non-virtual X11 display from the ambient DISPLAY env.

        Only set before Xvfb clobbers the environment; requires a socket in
        /tmp/.X11-unix that is not the Xvfb display itself.

        Returns:
            The DISPLAY value (e.g. ":0") or None if nothing usable is visible.
        """
        ambient = os.environ.get("DISPLAY")
        if not ambient:
            return None
        match = re.fullmatch(r":(\d+)", ambient)
        if not match:
            return None
        number = int(match.group(1))
        if number == self._display_num:
            return None
        if os.path.exists(f"/tmp/.X11-unix/X{number}"):
            return ambient
        return None

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
        """Capture the current screen as base64 PNG.

        Honors the configured capture mode: virtual, real, or auto
        (real display first, Xvfb as fallback). Uses grim for Wayland
        and X11 methods for X11 sessions.

        Returns:
            Base64-encoded PNG image string.

        Raises:
            DisplayError: If capture fails for the requested mode.
        """
        if not self.is_running:
            raise DisplayError("Cannot capture screenshot: Xvfb is not running")

        if self._capture_mode is CaptureMode.VIRTUAL:
            return await capture_x11_screenshot(self.display_var, self._width, self._height)

        if self._capture_mode is CaptureMode.REAL:
            if self._real_display is None:
                raise DisplayError(
                    "CaptureMode.REAL requires a visible real display, none detected"
                )
            return await capture_screenshot(self._real_display, self._width, self._height)

        if self._real_display is not None:
            try:
                return await capture_screenshot(self._real_display, self._width, self._height)
            except DisplayError as exc:
                logger.warning("Real display capture failed, using virtual: %s", exc)

        return await capture_x11_screenshot(self.display_var, self._width, self._height)

    async def _find_available_display(self) -> int:
        """Find an available DISPLAY number starting from :99."""
        for num in range(99, 200):
            sock_path = f"/tmp/.X11-unix/X{num}"
            if not os.path.exists(sock_path):
                return num
        raise DisplayError("No available DISPLAY number found (99-199)")
