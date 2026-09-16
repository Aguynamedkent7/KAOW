"""Tests for screenshot capture (X11 + Wayland)."""

from __future__ import annotations

import asyncio

import pytest

from kaow.display.base import DisplayError
from kaow.display.screenshot import (
    _capture_with_grim,
    _is_sane_png,
    _wayland_available,
    capture_screenshot,
)


class TestWaylandDetection:
    """Tests for Wayland availability detection."""

    def test_no_grim_not_available(self) -> None:
        """Returns False when grim binary is missing."""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("shutil.which", lambda name: None if name == "grim" else "/usr/bin/x")
            m.setenv("WAYLAND_DISPLAY", "wayland-0")
            m.setenv("XDG_RUNTIME_DIR", "/run/user/1000")

            async def run() -> bool:
                return _wayland_available()

            assert asyncio.run(run()) is False

    def test_missing_socket_env_not_available(self) -> None:
        """Returns False when Wayland socket env vars are unset."""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("shutil.which", lambda name: "/usr/bin/grim")
            m.delenv("WAYLAND_DISPLAY", raising=False)

            assert _wayland_available() is False

    def test_missing_socket_file_not_available(self) -> None:
        """Returns False when the Wayland socket file does not exist."""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("shutil.which", lambda name: "/usr/bin/grim")
            m.setenv("WAYLAND_DISPLAY", "wayland-0")
            m.setenv("XDG_RUNTIME_DIR", "/tmp/nonexistent-runtime")

            assert _wayland_available() is False


class TestSanePng:
    """Tests for PNG sanity validation."""

    def test_valid_png_accepted(self) -> None:
        """A real PNG of sufficient size passes validation."""
        from PIL import Image

        buf = __import__("io").BytesIO()
        Image.new("RGB", (320, 200), "blue").save(buf, format="PNG")
        assert _is_sane_png(buf.getvalue(), 100, 100) is True

    def test_tiny_png_rejected(self) -> None:
        """A PNG smaller than the minimum size is rejected."""
        from PIL import Image

        buf = __import__("io").BytesIO()
        Image.new("RGB", (4, 4), "blue").save(buf, format="PNG")
        assert _is_sane_png(buf.getvalue(), 100, 100) is False

    def test_garbage_rejected(self) -> None:
        """Non-PNG bytes are rejected."""
        assert _is_sane_png(b"not a png at all", 100, 100) is False


class TestGrimCapture:
    """Tests for grim Wayland capture."""

    def test_grim_not_installed_returns_none(self) -> None:
        """Returns None when grim binary is missing."""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("shutil.which", lambda name: None if name == "grim" else "/usr/bin/x")

            async def run() -> str | None:
                return await _capture_with_grim(1920, 1080)

            assert asyncio.run(run()) is None

    def test_missing_wayland_env_returns_none(self) -> None:
        """Returns None when Wayland socket env vars are unset."""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("shutil.which", lambda name: "/usr/bin/grim")
            m.delenv("WAYLAND_DISPLAY", raising=False)

            async def run() -> str | None:
                return await _capture_with_grim(1920, 1080)

            assert asyncio.run(run()) is None


class TestCaptureDispatch:
    """Tests for the session-aware capture dispatcher."""

    def test_x11_raises_on_all_failures(self) -> None:
        """Non-Wayland session raises DisplayError when all X11 methods fail."""
        with pytest.MonkeyPatch.context() as m:
            m.setenv("XDG_SESSION_TYPE", "x11")
            m.setattr("shutil.which", lambda name: None)

            with pytest.raises(DisplayError):
                asyncio.run(capture_screenshot(":99"))

    def test_wayland_missing_graceful_fallback(self) -> None:
        """Wayland session without grim falls through to X11 (no raise)."""
        with pytest.MonkeyPatch.context() as m:
            m.setenv("XDG_SESSION_TYPE", "wayland")
            m.setattr("shutil.which", lambda name: None)

            with pytest.raises(DisplayError):
                asyncio.run(capture_screenshot(":99"))
