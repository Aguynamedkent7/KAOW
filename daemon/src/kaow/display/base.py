"""Abstract base class for virtual display managers.

Display managers are responsible for providing a virtual framebuffer
so headless systems can render GUI elements for screenshot capture.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DisplayError(Exception):
    """Raised when a display operation fails."""


class DisplayManager(ABC):
    """Abstract interface for virtual display management.

    Subclasses must implement lifecycle methods (start/stop) and
    screenshot capture for the virtual framebuffer.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start the virtual display.

        Raises:
            DisplayError: If the display fails to start.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def stop(self) -> None:
        """Stop the virtual display and clean up resources."""
        ...  # pragma: no cover

    @abstractmethod
    async def set_resolution(self, width: int, height: int) -> None:
        """Change the virtual display resolution.

        Args:
            width: Display width in pixels.
            height: Display height in pixels.

        Raises:
            DisplayError: If the resolution change fails.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def capture_screenshot(self) -> str:
        """Capture the current framebuffer as a base64-encoded PNG.

        Returns:
            Base64-encoded PNG image data.

        Raises:
            DisplayError: If screenshot capture fails.
        """
        ...  # pragma: no cover

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the virtual display is currently active."""
        ...  # pragma: no cover
