"""KAOW configuration — all settings loaded from environment variables."""

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings


class CLIAdapterType(StrEnum):
    """Supported AI CLI adapters."""

    CLAUDE = "claude"
    OPENDEVIN = "opendevin"


class RelayMode(StrEnum):
    """How the daemon connects to clients."""

    LOCAL = "local"        # Direct WebSocket only (Phase 1)
    CLOUD = "cloud"        # Supabase relay (Phase 2)
    BOTH = "both"          # Local WS + Supabase relay


class Settings(BaseSettings):
    """Daemon settings, populated from environment variables or .env file."""

    model_config = {"env_prefix": "KAOW_", "env_file": ".env", "env_file_encoding": "utf-8"}

    host: str = Field(default="0.0.0.0", description="WebSocket server bind address")
    port: int = Field(default=8765, description="WebSocket server port")
    auth_token: str = Field(..., description="Bearer token for local WS auth")
    cli_adapter: CLIAdapterType = Field(
        default=CLIAdapterType.CLAUDE,
        description="Which AI CLI adapter to use",
    )
    cli_path: str = Field(default="claude", description="Path to the AI CLI binary")
    display_resolution: str = Field(
        default="1920x1080",
        description="Virtual display resolution (WxH)",
    )
    screenshot_interval: int = Field(
        default=5,
        description="Seconds between automatic screenshots",
    )
    log_level: str = Field(default="INFO", description="Logging level")

    # Relay mode
    relay_mode: RelayMode = Field(
        default=RelayMode.LOCAL,
        description="Connection mode: local, cloud, or both",
    )

    # Supabase (required when relay_mode is cloud or both)
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_service_key: str = Field(
        default="",
        description="Supabase service_role key (daemon uses this to bypass RLS)",
    )
    supabase_anon_key: str = Field(default="", description="Supabase anon/public key")

    # Device identity (for Supabase registration)
    device_name: str = Field(default="My PC", description="Device name shown in mobile app")
    device_user_id: str = Field(
        default="",
        description="Supabase user_id this device is paired to (set after QR pairing)",
    )

    @property
    def display_width(self) -> int:
        """Parse width from display_resolution."""
        return int(self.display_resolution.split("x")[0])

    @property
    def display_height(self) -> int:
        """Parse height from display_resolution."""
        return int(self.display_resolution.split("x")[1])


def load_settings() -> Settings:
    """Load and validate settings from environment.

    Required fields (e.g., AUTH_TOKEN) are populated from env vars /
    .env file at runtime, which mypy cannot see.
    """
    return Settings()  # type: ignore[call-arg]
