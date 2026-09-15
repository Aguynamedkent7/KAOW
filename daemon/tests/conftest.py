"""Shared test fixtures for KAOW daemon tests."""

from __future__ import annotations

import pytest

from kaow.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with a known auth token."""
    return Settings(
        auth_token="test-token-12345",
        host="127.0.0.1",
        port=8765,
        cli_adapter="claude",
        cli_path="/usr/bin/echo",
        display_resolution="640x480",
        screenshot_interval=1,
        log_level="DEBUG",
    )
