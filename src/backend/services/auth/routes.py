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

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.services.auth.models import (
    PasswordChange,
    User,
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
from backend.shared.config import settings
from backend.shared.email import send_otp_email
from backend.shared.otp import generate_otp, store_otp, verify_otp

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


class SendOtpRequest(BaseModel):
    """Request to send OTP."""
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    """Request to verify OTP."""
    email: EmailStr
    code: str


class OtpResponse(BaseModel):
    """Response for OTP operations."""
    message: str
    expires_in_minutes: int


class GoogleLoginRequest(BaseModel):
    """Request for Google social login."""
    id_token: str | None = None
    access_token: str | None = None
    email: EmailStr
    name: str
    picture: str | None = None


class ResetPasswordRequest(BaseModel):
    """Request to reset password after OTP verification."""
    email: EmailStr
    new_password: str


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


# ==================================================
# 🔢 OTP ENDPOINTS
# ==================================================

@router.post(
    "/send-otp",
    response_model=OtpResponse,
    summary="Send OTP verification code",
)
async def send_otp(request: SendOtpRequest) -> OtpResponse:
    """
    Send a one-time password to the specified email.
    
    - **email**: Email address to send OTP to
    
    The OTP expires after the configured time (default: 5 minutes).
    """
    # Generate and store OTP
    otp_code = generate_otp(settings.OTP_LENGTH)
    await store_otp(request.email, otp_code)
    
    # Send email
    success = await send_otp_email(request.email, otp_code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )
    
    return OtpResponse(
        message="Verification code sent to your email",
        expires_in_minutes=settings.OTP_EXPIRE_MINUTES,
    )


@router.post(
    "/verify-otp",
    response_model=MessageResponse,
    summary="Verify OTP code",
)
async def verify_otp_code(request: VerifyOtpRequest) -> MessageResponse:
    """
    Verify the OTP code sent to email.
    
    - **email**: Email address the OTP was sent to
    - **code**: The 6-digit OTP code
    
    On success, the user's email is marked as verified.
    """
    is_valid = await verify_otp(request.email, request.code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )
    
    # Mark user as verified
    user = await User.find_one(User.email == request.email)
    if user:
        user.is_verified = True
        await user.save()
    
    return MessageResponse(message="Email verified successfully")


# ==================================================
# 🌐 SOCIAL LOGIN ENDPOINTS
# ==================================================

@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Login/Register with Google",
)
async def google_login(request: GoogleLoginRequest) -> AuthResponse:
    """
    Login or register using Google OAuth.
    
    - If user exists, log them in
    - If user doesn't exist, create account and log them in
    - Google users are automatically marked as verified
    """
    from backend.shared.auth import create_token_pair
    
    # Check if user already exists
    user = await User.find_one(User.email == request.email)
    
    if user:
        # Existing user - update avatar if provided
        if request.picture and not user.avatar_url:
            user.avatar_url = request.picture
            await user.save()
    else:
        # New user - create account (no password needed for social login)
        import secrets
        user = User(
            email=request.email,
            name=request.name,
            password_hash=f"google:{secrets.token_hex(32)}",  # Placeholder, can't login with password
            avatar_url=request.picture,
            is_verified=True,  # Google emails are pre-verified
        )
        await user.insert()
    
    # Generate tokens
    tokens = create_token_pair(str(user.id))
    
    return AuthResponse(
        user=UserResponse.from_document(user),
        tokens=tokens,
    )


# ==================================================
# 🔑 RESET PASSWORD ENDPOINT
# ==================================================

@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password after OTP verification",
)
async def reset_password(request: ResetPasswordRequest) -> MessageResponse:
    """
    Reset user password after OTP verification.
    
    This endpoint should only be called AFTER the user has verified their 
    email via OTP from the forgot-password flow.
    
    - **email**: The user's email address
    - **new_password**: The new password (min 8 characters)
    """
    from backend.shared.auth import hash_password
    
    # Validate password length
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    
    # Find user by email
    user = await User.find_one(User.email == request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Hash and update password
    user.password_hash = hash_password(request.new_password)
    await user.save()
    
    return MessageResponse(message="Password reset successfully")
