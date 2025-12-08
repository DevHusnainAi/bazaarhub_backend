"""
👤 USER MODEL (Auth Service)
============================

🎯 PURPOSE:
MongoDB document model for users using Beanie ODM.

✅ BEST PRACTICES:
1. Use Beanie Document for MongoDB integration with FastAPI
2. Create database indexes for frequently queried fields
3. Never expose password_hash in API responses
4. Use Pydantic's model_config to control serialization

❌ BAD PRACTICES:
- Storing plain-text passwords (always hash!)
- No indexes on email (slow login lookups with millions of users)
- Returning password_hash in responses (security vulnerability)

📚 BEANIE CONCEPTS:
- Document: MongoDB document (like a table row in SQL)
- Indexed: Creates a database index for fast lookups
- Settings: Configure collection name and indexes
"""

from datetime import datetime

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


class User(Document):
    """
    User document stored in MongoDB.
    
    ✅ COLLECTION: users
    ✅ INDEXES: email (unique)
    """
    # ✅ BEST PRACTICE: Use EmailStr for automatic email validation
    email: Indexed(EmailStr, unique=True)  # type: ignore
    password_hash: str  # Never expose in API responses (use response models)
    
    # Profile info
    name: str
    phone: str | None = None
    avatar_url: str | None = None
    
    # Account status
    is_active: bool = True
    is_verified: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime | None = None
    
    class Settings:
        # ✅ BEST PRACTICE: Explicit collection name
        name = "users"
        # ✅ BEST PRACTICE: Use validation on insert/update
        use_state_management = True
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


# ==================================================
# 📤 RESPONSE SCHEMAS (what API returns)
# ==================================================

class UserResponse(BaseModel):
    """
    User data returned in API responses.
    
    ✅ BEST PRACTICE: Separate response model that excludes sensitive data
    """
    id: str
    email: EmailStr
    name: str
    phone: str | None = None
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    @classmethod
    def from_document(cls, user: User) -> "UserResponse":
        """Create response from User document."""
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )


class UserProfileResponse(BaseModel):
    """Extended user profile for the current user."""
    id: str
    email: EmailStr
    name: str
    phone: str | None = None
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None
    
    @classmethod
    def from_document(cls, user: User) -> "UserProfileResponse":
        """Create profile response from User document."""
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
        )


# ==================================================
# 📥 REQUEST SCHEMAS (what API receives)
# ==================================================

class UserCreate(BaseModel):
    """
    Schema for user registration.
    
    ✅ BEST PRACTICE: Validate input with Pydantic
    - EmailStr validates email format
    - Field() adds constraints like min_length
    """
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    
    ✅ BEST PRACTICE: All fields optional for partial updates
    """
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    avatar_url: str | None = None


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(min_length=8)
