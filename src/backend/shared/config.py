"""
⚙️ SHARED CONFIGURATION MODULE
================================

🎯 PURPOSE:
This module handles all environment-based configuration for the microservices.
It follows the 12-Factor App methodology (https://12factor.net/config).

✅ BEST PRACTICE:
- Never hardcode secrets or configuration values in code
- Use environment variables for all config that varies between environments
- Validate config at startup (fail fast if missing required values)

❌ BAD PRACTICE:
- Hardcoding: `MONGODB_URI = "mongodb://localhost:27017"`
- No validation: Just using `os.getenv()` without defaults or validation
- Scattered config: Having config values spread across multiple files

📚 LEARN MORE:
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- 12-Factor Config: https://12factor.net/config
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, MongoDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    ✅ BEST PRACTICE: Use Pydantic Settings for:
    - Type validation (catches config errors at startup)
    - Default values (development-friendly)
    - Documentation (each field is self-documenting)
    """
    
    # --------------------------------------------------
    # 🏷️ APPLICATION INFO
    # --------------------------------------------------
    APP_NAME: str = "E-commerce API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    
    # --------------------------------------------------
    # 🗃️ DATABASE CONFIGURATION
    # --------------------------------------------------
    # ✅ BEST PRACTICE: Use connection string format for flexibility
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string (use MongoDB Atlas URI in production)"
    )
    MONGODB_DATABASE: str = Field(
        default="ecommerce",
        description="Database name"
    )
    
    # --------------------------------------------------
    # 🔴 REDIS CONFIGURATION (for caching)
    # --------------------------------------------------
    REDIS_URI: str = Field(
        default="redis://localhost:6379",
        description="Redis connection string"
    )
    
    # --------------------------------------------------
    # 🔐 SECURITY / JWT CONFIGURATION
    # --------------------------------------------------
    # ✅ BEST PRACTICE: Long, random secret key (use `openssl rand -hex 32` to generate)
    JWT_SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32",
        description="Secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # --------------------------------------------------
    # 🌐 CORS CONFIGURATION
    # --------------------------------------------------
    # ✅ BEST PRACTICE: Restrict origins in production
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8081"],
        description="Allowed CORS origins (add your mobile app URL in production)"
    )
    
    # --------------------------------------------------
    # 📧 EMAIL CONFIGURATION (Brevo/Sendinblue)
    # --------------------------------------------------
    BREVO_API_KEY: str = Field(
        default="",
        description="Brevo API key for sending emails"
    )
    BREVO_SENDER_NAME: str = "BazaarHub"
    BREVO_SENDER_EMAIL: str = "noreply@bazaarhub.com"
    
    # --------------------------------------------------
    # 🔢 OTP CONFIGURATION
    # --------------------------------------------------
    OTP_EXPIRE_MINUTES: int = Field(
        default=5,
        description="OTP expiration time in minutes"
    )
    OTP_LENGTH: int = 6
    
    # --------------------------------------------------
    # 📊 SERVICE PORTS (for microservices)
    # --------------------------------------------------
    AUTH_SERVICE_PORT: int = 8001
    PRODUCT_SERVICE_PORT: int = 8002
    CART_SERVICE_PORT: int = 8003
    ORDER_SERVICE_PORT: int = 8004
    
    # --------------------------------------------------
    # ⚙️ PYDANTIC SETTINGS CONFIG
    # --------------------------------------------------
    model_config = SettingsConfigDict(
        # ✅ BEST PRACTICE: Load from .env file
        env_file=".env",
        env_file_encoding="utf-8",
        # ✅ BEST PRACTICE: Allow extra fields (flexibility for different envs)
        extra="ignore",
        # ✅ BEST PRACTICE: Case-insensitive env vars
        case_sensitive=False,
    )


# ✅ BEST PRACTICE: Use lru_cache to avoid re-reading .env on every request
@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using @lru_cache ensures we only parse environment variables once,
    not on every request. This is a significant performance optimization.
    """
    return Settings()


# Export a singleton for convenience
settings = get_settings()
