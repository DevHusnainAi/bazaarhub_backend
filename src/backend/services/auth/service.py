"""
🔐 AUTH SERVICE (Business Logic)
=================================

🎯 PURPOSE:
Handle user registration, authentication, and profile management.

✅ BEST PRACTICES:
1. Separate business logic from routes (testable, reusable)
2. Raise custom exceptions for different error cases
3. Don't expose whether email exists (security)
4. Rate limit login attempts (not implemented here, use middleware)

❌ BAD PRACTICES:
- Putting all logic in route handlers (hard to test)
- Returning "email already exists" (helps attackers enumerate users)
- No password validation rules
"""

from datetime import datetime

from fastapi import HTTPException, status

from backend.services.auth.models import (
    PasswordChange,
    User,
    UserCreate,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from backend.shared.auth import (
    TokenPair,
    create_token_pair,
    hash_password,
    verify_password,
)
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service handling user operations.
    
    ✅ BEST PRACTICE: Service class pattern
    - Encapsulates business logic
    - Easy to mock in tests
    - Reusable across different interfaces (API, CLI, etc.)
    """
    
    async def register(self, user_data: UserCreate) -> tuple[UserResponse, TokenPair]:
        """
        Register a new user.
        
        Args:
            user_data: Registration data (email, password, name)
            
        Returns:
            Tuple of (user_response, token_pair)
            
        Raises:
            HTTPException 400: If email already registered
        """
        logger.info("Registering new user", email=user_data.email)
        
        # Check if email already exists
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            logger.warning("Registration failed: email exists", email=user_data.email)
            # ✅ BEST PRACTICE: Generic message (don't confirm email exists)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to create account with this email",
            )
        
        # ✅ BEST PRACTICE: Hash password before storing
        password_hash = hash_password(user_data.password)
        
        # Create user document
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            name=user_data.name,
        )
        
        # Save to database
        await user.insert()
        logger.info("User registered successfully", user_id=str(user.id))
        
        # Create tokens
        tokens = create_token_pair(str(user.id))
        
        return UserResponse.from_document(user), tokens
    
    async def login(self, email: str, password: str) -> tuple[UserResponse, TokenPair]:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Tuple of (user_response, token_pair)
            
        Raises:
            HTTPException 401: If credentials are invalid
        """
        logger.info("Login attempt", email=email)
        
        # Find user by email
        user = await User.find_one(User.email == email)
        
        # ✅ BEST PRACTICE: Same error for "user not found" and "wrong password"
        # This prevents attackers from knowing if an email is registered
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Login failed: invalid credentials", email=email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Check if account is active
        if not user.is_active:
            logger.warning("Login failed: account deactivated", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account has been deactivated",
            )
        
        # Update last login timestamp
        user.last_login = datetime.now()
        await user.save()
        
        logger.info("Login successful", user_id=str(user.id))
        
        # Create tokens
        tokens = create_token_pair(str(user.id))
        
        return UserResponse.from_document(user), tokens
    
    async def get_profile(self, user_id: str) -> UserProfileResponse:
        """
        Get user's profile.
        
        Args:
            user_id: Current user's ID
            
        Returns:
            User profile data
            
        Raises:
            HTTPException 404: If user not found
        """
        user = await User.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return UserProfileResponse.from_document(user)
    
    async def update_profile(
        self,
        user_id: str,
        update_data: UserUpdate,
    ) -> UserProfileResponse:
        """
        Update user's profile.
        
        Args:
            user_id: Current user's ID
            update_data: Fields to update
            
        Returns:
            Updated user profile
        """
        user = await User.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # ✅ BEST PRACTICE: Only update fields that were provided
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if update_dict:
            for field, value in update_dict.items():
                setattr(user, field, value)
            user.update_timestamp()
            await user.save()
            
            logger.info("Profile updated", user_id=user_id, fields=list(update_dict.keys()))
        
        return UserProfileResponse.from_document(user)
    
    async def change_password(
        self,
        user_id: str,
        password_data: PasswordChange,
    ) -> None:
        """
        Change user's password.
        
        Args:
            user_id: Current user's ID
            password_data: Current and new password
            
        Raises:
            HTTPException 400: If current password is wrong
        """
        user = await User.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        
        # Hash and save new password
        user.password_hash = hash_password(password_data.new_password)
        user.update_timestamp()
        await user.save()
        
        logger.info("Password changed", user_id=user_id)
    
    async def refresh_tokens(self, user_id: str) -> TokenPair:
        """
        Generate new token pair for existing user.
        
        ✅ USE CASE: Called when access token expires
        
        Args:
            user_id: User ID from refresh token
            
        Returns:
            New token pair
        """
        user = await User.get(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        return create_token_pair(str(user.id))


# ✅ BEST PRACTICE: Singleton instance for dependency injection
auth_service = AuthService()
