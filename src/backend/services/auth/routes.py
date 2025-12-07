"""
🛣️ AUTH SERVICE ROUTES
=======================

🎯 PURPOSE:
API endpoints for authentication operations.

✅ BEST PRACTICES:
1. Use proper HTTP methods (POST for create, GET for read, etc.)
2. Use proper status codes (201 for created, 401 for unauthorized)
3. Document endpoints with docstrings (auto-generates OpenAPI docs)
4. Keep routes thin - delegate logic to service layer

❌ BAD PRACTICES:
- Putting business logic in routes (hard to test)
- Using GET for login (passwords in URL = security risk)
- Same status code for all responses (unhelpful for clients)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.services.auth.models import (
    PasswordChange,
    UserCreate,
    UserLogin,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from backend.services.auth.service import auth_service
from backend.shared.auth import (
    CurrentUserId,
    RefreshTokenPayload,
    TokenPair,
)

# ✅ BEST PRACTICE: Use router with prefix and tags for organization
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================================================
# 📤 RESPONSE MODELS
# ==================================================

class AuthResponse(BaseModel):
    """Response for login/register endpoints."""
    user: UserResponse
    tokens: TokenPair


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# ==================================================
# 🛣️ ENDPOINTS
# ==================================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(user_data: UserCreate) -> AuthResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters
    - **name**: User's display name
    
    Returns user data and authentication tokens.
    """
    user, tokens = await auth_service.register(user_data)
    return AuthResponse(user=user, tokens=tokens)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
)
async def login(credentials: UserLogin) -> AuthResponse:
    """
    Authenticate user with email and password.
    
    Returns user data and authentication tokens.
    Use the access_token in the Authorization header for authenticated requests:
    `Authorization: Bearer <access_token>`
    """
    user, tokens = await auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )
    return AuthResponse(user=user, tokens=tokens)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh access token",
)
async def refresh_token(token_payload: RefreshTokenPayload) -> TokenPair:
    """
    Get new tokens using a refresh token.
    
    Send the refresh_token in the Authorization header:
    `Authorization: Bearer <refresh_token>`
    
    Returns a new token pair (both access and refresh tokens).
    """
    return await auth_service.refresh_tokens(token_payload.sub)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user's profile",
)
async def get_profile(user_id: CurrentUserId) -> UserProfileResponse:
    """
    Get the current authenticated user's profile.
    
    Requires valid access token in Authorization header.
    """
    return await auth_service.get_profile(user_id)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    summary="Update current user's profile",
)
async def update_profile(
    user_id: CurrentUserId,
    update_data: UserUpdate,
) -> UserProfileResponse:
    """
    Update the current user's profile.
    
    Only provided fields will be updated (partial update).
    """
    return await auth_service.update_profile(user_id, update_data)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
)
async def change_password(
    user_id: CurrentUserId,
    password_data: PasswordChange,
) -> MessageResponse:
    """
    Change the current user's password.
    
    Requires current password for verification.
    """
    await auth_service.change_password(user_id, password_data)
    return MessageResponse(message="Password changed successfully")
