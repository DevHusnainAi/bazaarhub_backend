"""
🔐 AUTH MODULE
==============

JWT authentication and password utilities.
"""

from backend.shared.auth.dependencies import (
    CurrentUserId,
    OptionalUserId,
    RefreshTokenPayload,
    get_current_user_id,
    get_current_user_optional,
    verify_refresh_token,
)
from backend.shared.auth.jwt import (
    TokenPair,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
    verify_token,
)

__all__ = [
    # JWT
    "TokenPair",
    "TokenPayload",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "hash_password",
    "verify_password",
    "verify_token",
    # Dependencies
    "CurrentUserId",
    "OptionalUserId",
    "RefreshTokenPayload",
    "get_current_user_id",
    "get_current_user_optional",
    "verify_refresh_token",
]
