"""Tests for KAOW CLI adapters."""

from __future__ import annotations

import pytest

from kaow.adapters.base import AdapterError, CLIAdapter
from kaow.adapters.claude import ClaudeAdapter
from kaow.adapters.opencode import OpenCodeAdapter
from kaow.config import CLIAdapterType


class TestCLIAdapterBase:
    """Tests for the abstract CLIAdapter interface."""

    def test_cannot_instantiate_abstract(self) -> None:
        """CLIAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CLIAdapter()  # type: ignore[abstract]


class TestClaudeAdapter:
    """Tests for the Claude CLI adapter."""

    def test_init_default_path(self) -> None:
        """Default CLI path is 'claude'."""
        adapter = ClaudeAdapter()
        assert adapter._cli_path == "claude"

    def test_init_custom_path(self) -> None:
        """Custom CLI path is stored."""
        adapter = ClaudeAdapter(cli_path="/usr/local/bin/claude")
        assert adapter._cli_path == "/usr/local/bin/claude"

    @pytest.mark.asyncio
    async def test_health_check_no_binary(self) -> None:
        """Health check returns False when CLI binary not found."""
        adapter = ClaudeAdapter(cli_path="/nonexistent/binary")
        result = await adapter.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_no_binary_raises(self) -> None:
        """Execute raises AdapterError when CLI binary not found."""
        adapter = ClaudeAdapter(cli_path="/nonexistent/binary")
        with pytest.raises(AdapterError, match="not found"):
            async for _ in adapter.execute("test prompt"):
                pass

    @pytest.mark.asyncio
    async def test_kill_empty_processes(self) -> None:
        """Kill returns False when no processes are running."""
        adapter = ClaudeAdapter()
        result = await adapter.kill("any-task-id")
        assert result is False


class TestOpenCodeAdapter:
    """Tests for the opencode CLI adapter."""

    def test_default_path(self) -> None:
        """Default CLI path is 'opencode'."""
        assert OpenCodeAdapter()._cli_path == "opencode"

    @pytest.mark.asyncio
    async def test_health_check_no_binary(self) -> None:
        """Health check returns False when CLI binary not found."""
        adapter = OpenCodeAdapter(cli_path="/nonexistent/binary")
        result = await adapter.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_no_binary_raises(self) -> None:
        """Execute raises AdapterError when CLI binary not found."""
        adapter = OpenCodeAdapter(cli_path="/nonexistent/binary")
        with pytest.raises(AdapterError, match="not found"):
            async for _ in adapter.execute("test prompt"):
                pass

    def test_adapter_enum_value(self) -> None:
        """The opencode adapter type string matches the config enum."""
        assert CLIAdapterType.OPENCODE.value == "opencode"
