"""
🔢 OTP SERVICE
==============

🎯 PURPOSE:
Generate, store, and verify OTP codes using Redis for temporary storage.

✅ BEST PRACTICES:
1. Use Redis for OTP storage (automatic expiration)
2. Generate cryptographically secure random codes
3. Delete OTP immediately after successful verification
4. Rate limit OTP requests to prevent abuse
"""

import secrets

import redis.asyncio as redis

from backend.shared.config import settings

# Redis client (lazy initialization)
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URI,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure OTP code.
    
    Args:
        length: Number of digits in the OTP
        
    Returns:
        Random numeric string of specified length
    """
    # Generate random digits
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


async def store_otp(email: str, otp: str, expire_minutes: int | None = None) -> None:
    """
    Store OTP in Redis with expiration.
    
    Args:
        email: User's email address (used as key)
        otp: The OTP code to store
        expire_minutes: Expiration time (defaults to settings)
    """
    if expire_minutes is None:
        expire_minutes = settings.OTP_EXPIRE_MINUTES
    
    client = await get_redis_client()
    key = f"otp:{email}"
    
    # Store with expiration
    await client.setex(
        name=key,
        time=expire_minutes * 60,  # Convert to seconds
        value=otp,
    )


async def verify_otp(email: str, otp: str) -> bool:
    """
    Verify an OTP code.
    
    Args:
        email: User's email address
        otp: The OTP code to verify
        
    Returns:
        True if valid, False otherwise
    """
    client = await get_redis_client()
    key = f"otp:{email}"
    
    stored_otp = await client.get(key)
    
    if stored_otp is None:
        return False
    
    if stored_otp == otp:
        # Delete OTP after successful verification
        await client.delete(key)
        return True
    
    return False


async def delete_otp(email: str) -> None:
    """Delete OTP for an email (cleanup)."""
    client = await get_redis_client()
    key = f"otp:{email}"
    await client.delete(key)


async def get_otp_ttl(email: str) -> int:
    """
    Get remaining time-to-live for an OTP.
    
    Returns:
        Seconds remaining, or -1 if not found
    """
    client = await get_redis_client()
    key = f"otp:{email}"
    return await client.ttl(key)
