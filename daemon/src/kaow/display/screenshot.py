"""Screenshot capture — captures X11 framebuffer as base64-encoded PNG."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import shutil

from kaow.display.base import DisplayError

logger = logging.getLogger(__name__)


async def capture_x11_screenshot(
    display: str,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Capture a screenshot from an X11 display as base64 PNG.

    Tries multiple methods in order:
    1. import (ImageMagick)
    2. xdotool + scrot
    3. PIL/Pillow with Xlib

    Args:
        display: The DISPLAY environment variable value (e.g., ":99").
        width: Expected screenshot width for validation.
        height: Expected screenshot height for validation.

    Returns:
        Base64-encoded PNG image data.

    Raises:
        DisplayError: If all capture methods fail.
    """
    methods = [
        _capture_with_import,
        _capture_with_scrot,
        _capture_with_pillow,
    ]

    last_error: Exception | None = None
    for method in methods:
        try:
            result = await method(display, width, height)
            if result:
                return result
        except Exception as exc:
            last_error = exc
            logger.debug("Screenshot method %s failed: %s", method.__name__, exc)

    raise DisplayError(f"All screenshot methods failed. Last error: {last_error}")


async def _capture_with_import(display: str, width: int, height: int) -> str | None:
    """Capture using ImageMagick's import command."""
    if not shutil.which("import"):
        return None

    env = {"DISPLAY": display}
    cmd = ["import", "-window", "root", "png:-"]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**__import__("os").environ, **env},
    )
    stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10.0)

    if process.returncode != 0 or not stdout:
        return None

    return base64.b64encode(stdout).decode("ascii")


async def _capture_with_scrot(display: str, width: int, height: int) -> str | None:
    """Capture using scrot (Screenshot utility)."""
    if not shutil.which("scrot"):
        return None

    import os
    import tempfile

    env = {**os.environ, "DISPLAY": display}
    with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
        cmd = ["scrot", "-o", tmp.name]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        await asyncio.wait_for(process.communicate(), timeout=10.0)

        if process.returncode != 0:
            return None

        data = tmp.read()
        if not data:
            return None

        return base64.b64encode(data).decode("ascii")


async def _capture_with_pillow(display: str, width: int, height: int) -> str | None:
    """Capture using PIL/Pillow — requires python-xlib or X11 bindings."""
    try:
        from PIL import Image

        try:
            from Xlib import display as xdisplay

            d = xdisplay.Display(display)
            root = d.screen().root
            raw = root.get_image(0, 0, width, height, 0x00000004, 0xFFFFFFFF)
            img = Image.frombytes("RGB", (width, height), raw.data, "raw", "BGRX")
        except ImportError:
            logger.debug("python-xlib not available, trying scrot fallback")
            return None

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    except ImportError:
        logger.debug("Pillow not available for screenshot capture")
        return None
