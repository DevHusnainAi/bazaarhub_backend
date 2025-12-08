"""
🔐 JWT AUTHENTICATION MODULE
============================

🎯 PURPOSE:
Handle JWT token creation, validation, and password hashing.

✅ BEST PRACTICES:
1. Use bcrypt for password hashing (slow by design = secure)
2. Short-lived access tokens (30 min) + long-lived refresh tokens (7 days)
3. Include minimal claims in JWT (don't store sensitive data)
4. Use RS256 for multi-service setups (we use HS256 for simplicity here)

❌ BAD PRACTICES:
- MD5/SHA1 for passwords (too fast, easily cracked)
- Long-lived access tokens (if stolen, attacker has long access)
- Storing passwords in JWT (anyone can decode the payload)
- No token expiration (tokens valid forever)

📚 SECURITY CONCEPTS:
- Access Token: Short-lived, used for API authentication
- Refresh Token: Long-lived, used only to get new access tokens
- bcrypt: Adaptive hashing algorithm that's slow to prevent brute-force
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.shared.config import settings


class TokenPayload(BaseModel):
    """
    JWT token payload schema.
    
    ✅ BEST PRACTICE: Use Pydantic for token payload validation
    This ensures we catch malformed tokens early.
    """
    sub: str  # Subject (usually user ID)
    exp: datetime  # Expiration time
    type: str  # Token type: "access" or "refresh"
    

class TokenPair(BaseModel):
    """Response model for token endpoints."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ==================================================
# 🔒 PASSWORD HASHING FUNCTIONS
# ==================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    ✅ BEST PRACTICE: Never store plain-text passwords
    
    Args:
        password: Plain-text password
        
    Returns:
        Hashed password (safe to store in database)
        
    Example:
        hashed = hash_password("user_password123")
        # Returns something like: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJq...
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    ✅ BEST PRACTICE: Use constant-time comparison (bcrypt does this)
    This prevents timing attacks.
    
    Args:
        plain_password: Password to verify
        hashed_password: Stored hash from database
        
    Returns:
        True if password matches, False otherwise
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ==================================================
# 🎫 JWT TOKEN FUNCTIONS
# ==================================================

def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived access token.
    
    ✅ BEST PRACTICE: Short expiration (30 min default)
    If token is stolen, damage is limited.
    
    Args:
        subject: User identifier (usually user_id)
        expires_delta: Custom expiration time (optional)
        extra_claims: Additional data to include in token
        
    Returns:
        Encoded JWT access token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(UTC) + expires_delta
    
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "iat": datetime.now(UTC),  # Issued at
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived refresh token.
    
    ✅ BEST PRACTICE: 
    - Longer expiration (7 days default)
    - Only used to get new access tokens
    - Should be stored securely (httpOnly cookie or secure storage)
    
    Args:
        subject: User identifier
        
    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.now(UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(UTC),
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_token_pair(subject: str) -> TokenPair:
    """
    Create both access and refresh tokens.
    
    ✅ USE CASE: Login endpoint returns both tokens
    """
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.
    
    ✅ BEST PRACTICE: Validate token signature and expiration
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid, expired, or tampered with
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return TokenPayload(**payload)
    except JWTError:
        raise


def verify_token(token: str, expected_type: str = "access") -> TokenPayload | None:
    """
    Verify a token and check its type.
    
    ✅ BEST PRACTICE: Verify token type to prevent token confusion attacks
    (using refresh token as access token)
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.type != expected_type:
            return None
        return payload
    except JWTError:
        return None
