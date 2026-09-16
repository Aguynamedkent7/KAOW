"""Screenshot capture — captures X11 or Wayland framebuffer as base64 PNG."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import shutil

from kaow.display.base import DisplayError

logger = logging.getLogger(__name__)


def _wayland_available() -> bool:
    """Detect if grim can capture the current Wayland session.

    Unlike XDG_SESSION_TYPE (unreliable when the daemon runs detached),
    checks the concrete requirements: grim binary plus a live Wayland
    socket at $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY.
    """
    if not shutil.which("grim"):
        return False
    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not wayland_display or not xdg_runtime:
        return False
    return os.path.exists(os.path.join(xdg_runtime, wayland_display))


def _is_sane_png(data: bytes, min_width: int, min_height: int) -> bool:
    """Return True if data is a PNG of at least min_width x min_height.

    Guards against garbage captures (e.g. ImageMagick on an XWayland
    window) that decode to tiny or invalid images.
    """
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            return width >= min_width and height >= min_height
    except Exception:
        return False


async def capture_screenshot(
    display: str,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Capture a screenshot as base64 PNG, auto-detecting display server.

    Tries grim on a live Wayland session first, then the X11 methods
    (import/scrot/Pillow). Captures that fail PNG sanity checks are
    treated as failures so bad captures fall through.

    Args:
        display: The DISPLAY env var value (e.g., ":99") — used for X11 only.
        width: Expected screenshot width for validation.
        height: Expected screenshot height for validation.

    Returns:
        Base64-encoded PNG image data.

    Raises:
        DisplayError: If all capture methods fail.
    """
    if _wayland_available():
        result = await _capture_with_grim(width, height)
        if result:
            return result
        logger.warning("grim capture failed, falling back to X11 methods")

    return await capture_x11_screenshot(display, width, height)


async def capture_x11_screenshot(
    display: str,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Capture a screenshot from an X11 display as base64 PNG.

    Tries multiple methods in order:
    1. import (ImageMagick)
    2. scrot
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

    raise DisplayError(f"All X11 screenshot methods failed. Last error: {last_error}")


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
        env={**os.environ, **env},
    )
    stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10.0)

    if process.returncode != 0 or not stdout:
        return None
    if not _is_sane_png(stdout, width, height):
        logger.debug("import returned an invalid or undersized image")
        return None

    return base64.b64encode(stdout).decode("ascii")


async def _capture_with_scrot(display: str, width: int, height: int) -> str | None:
    """Capture using scrot (Screenshot utility)."""
    if not shutil.which("scrot"):
        return None

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
        if not _is_sane_png(data, width, height):
            logger.debug("scrot returned an invalid or undersized image")
            return None

        return base64.b64encode(data).decode("ascii")


async def _capture_with_grim(width: int, height: int) -> str | None:
    """Capture using grim — Wayland-native screenshot tool.

    Requires WAYLAND_DISPLAY and XDG_RUNTIME_DIR to be set.
    grim - png:- outputs PNG to stdout.
    """
    if not shutil.which("grim"):
        logger.debug("grim not found — install with: pacman -S grim")
        return None

    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not wayland_display or not xdg_runtime:
        logger.debug("WAYLAND_DISPLAY or XDG_RUNTIME_DIR not set")
        return None

    socket_path = os.path.join(xdg_runtime, wayland_display)
    if not os.path.exists(socket_path):
        logger.debug("Wayland socket not found: %s", socket_path)
        return None

    env = {**os.environ, "WAYLAND_DISPLAY": wayland_display}
    cmd = ["grim", "-g", f"0,0 {width}x{height}", "png:-"]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)

    if process.returncode != 0 or not stdout:
        logger.debug("grim failed (rc=%s): %s", process.returncode, stderr.decode(errors="replace"))
        return None
    if not _is_sane_png(stdout, width, height):
        logger.debug("grim returned an invalid or undersized image")
        return None

    return base64.b64encode(stdout).decode("ascii")


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
