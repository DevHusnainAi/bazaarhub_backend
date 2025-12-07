"""
🔑 AUTH DEPENDENCIES MODULE
===========================

🎯 PURPOSE:
FastAPI dependencies for protecting routes and extracting current user.

✅ BEST PRACTICES:
1. Use FastAPI's dependency injection for auth (clean, testable)
2. Extract user from token in a reusable dependency
3. Return proper HTTP 401/403 errors with clear messages
4. Support both required and optional auth

❌ BAD PRACTICES:
- Checking auth in every route handler (duplicated code)
- Returning 500 errors for auth failures (confusing)
- Not distinguishing between "not logged in" and "forbidden"

📚 HTTP STATUS CODES:
- 401 Unauthorized: Not logged in / invalid credentials
- 403 Forbidden: Logged in but not allowed to access resource
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.shared.auth.jwt import TokenPayload, verify_token

# ✅ BEST PRACTICE: Use HTTPBearer for JWT auth
# This extracts the token from "Authorization: Bearer <token>" header
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security)
    ],
) -> str:
    """
    Get the current authenticated user's ID from JWT token.
    
    ✅ BEST PRACTICE: Use as a dependency on protected routes
    
    Usage:
        @router.get("/profile")
        async def get_profile(user_id: str = Depends(get_current_user_id)):
            # user_id is guaranteed to be valid here
            ...
    
    Raises:
        HTTPException 401: If not authenticated or token invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token, expected_type="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload.sub


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security)
    ],
) -> str | None:
    """
    Get current user ID if authenticated, None otherwise.
    
    ✅ USE CASE: Routes that work for both guests and logged-in users
    
    Example:
        @router.get("/products")
        async def list_products(user_id: str | None = Depends(get_current_user_optional)):
            if user_id:
                # Show personalized recommendations
            else:
                # Show generic products
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_token(token, expected_type="access")
    
    return payload.sub if payload else None


async def verify_refresh_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security)
    ],
) -> TokenPayload:
    """
    Verify a refresh token for the token refresh endpoint.
    
    ✅ BEST PRACTICE: Separate dependency for refresh tokens
    This ensures refresh tokens can't be used as access tokens.
    
    Raises:
        HTTPException 401: If refresh token is invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token, expected_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


# ✅ BEST PRACTICE: Create type aliases for cleaner route signatures
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
OptionalUserId = Annotated[str | None, Depends(get_current_user_optional)]
RefreshTokenPayload = Annotated[TokenPayload, Depends(verify_refresh_token)]
