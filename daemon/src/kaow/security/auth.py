"""Authentication helpers — token validation for WebSocket connections."""

from __future__ import annotations

import hmac
import logging

logger = logging.getLogger(__name__)


def validate_token(provided: str | None, expected: str) -> bool:
    """Validate an authentication token using constant-time comparison.

    Args:
        provided: The token provided by the client.
        expected: The expected valid token.

    Returns:
        True if tokens match.
    """
    if provided is None:
        return False
    return hmac.compare_digest(provided.encode(), expected.encode())
