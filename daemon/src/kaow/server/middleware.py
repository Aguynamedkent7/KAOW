"""WebSocket authentication middleware — token validation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        self.message = message
        super().__init__(self.message)


def extract_token(websocket: WebSocket) -> str | None:
    """Extract bearer token from WebSocket connection query params or headers.

    Checks query param 'token' first, then Authorization header.
    """
    token = websocket.query_params.get("token")
    if token:
        return token

    auth_header = websocket.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None


def validate_token(token: str | None, expected_token: str) -> None:
    """Validate the provided token matches the expected token.

    Raises AuthError if validation fails.
    """
    if token is None:
        logger.warning("No authentication token provided")
        raise AuthError("No authentication token provided")

    if not _constant_time_compare(token, expected_token):
        logger.warning("Invalid authentication token")
        raise AuthError("Invalid authentication token")


def _constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    import hmac

    return hmac.compare_digest(val1.encode(), val2.encode())
