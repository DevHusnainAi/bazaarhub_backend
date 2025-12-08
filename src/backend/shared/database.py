"""
🗃️ DATABASE CONNECTION MODULE
==============================

🎯 PURPOSE:
This module manages MongoDB connections using Motor (async driver) and Beanie (ODM).

✅ BEST PRACTICES:
1. Connection Pooling: Reuse connections instead of creating new ones per request
2. Async Driver: Use Motor for non-blocking database operations
3. Health Checks: Verify database connectivity at startup
4. Graceful Shutdown: Properly close connections when the app stops

❌ BAD PRACTICES:
- Creating a new connection per request (performance killer)
- Using synchronous drivers with FastAPI (blocks the event loop)
- Not handling connection errors (app crashes silently)
- No connection timeout (hangs forever if DB is unreachable)

📚 LEARN MORE:
- Motor: https://motor.readthedocs.io/
- Beanie: https://beanie-odm.dev/
"""

from typing import TYPE_CHECKING

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from backend.shared.config import settings

if TYPE_CHECKING:
    from beanie import Document

# ✅ BEST PRACTICE: Module-level client (singleton pattern)
# This ensures we reuse the same connection pool across all requests
_client: AsyncIOMotorClient | None = None


async def init_database(document_models: list[type["Document"]]) -> None:
    """
    Initialize database connection and register document models.
    
    ✅ BEST PRACTICE: 
    - Call this during FastAPI startup event
    - Pass only the Document models this service needs (microservice isolation)
    
    Args:
        document_models: List of Beanie Document classes to register
        
    Example:
        @app.on_event("startup")
        async def startup():
            await init_database([User, Product])
    """
    global _client
    
    # ✅ BEST PRACTICE: Configure connection with sensible defaults
    import logging
    # Suppress verbose MongoDB driver logs
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    _client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        # Connection pool settings for scalability
        maxPoolSize=50,           # Max concurrent connections
        minPoolSize=10,           # Keep connections warm
        maxIdleTimeMS=30000,      # Close idle connections after 30s
        # Timeout settings (fail fast)
        serverSelectionTimeoutMS=5000,  # Give up after 5s if can't connect
        connectTimeoutMS=10000,         # Connection timeout
    )
    
    # ✅ BEST PRACTICE: Initialize Beanie ODM
    await init_beanie(
        database=_client[settings.MONGODB_DATABASE],
        document_models=document_models,
    )


async def close_database() -> None:
    """
    Close database connection gracefully.
    
    ✅ BEST PRACTICE: Call this during FastAPI shutdown event
    
    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_database()
    """
    global _client
    
    if _client is not None:
        _client.close()
        _client = None


async def check_database_health() -> dict:
    """
    Check database connectivity for health endpoints.
    
    ✅ BEST PRACTICE: Include in your /health endpoint for:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Monitoring systems
    
    Returns:
        dict: Health status with details
    """
    global _client
    
    if _client is None:
        return {"status": "unhealthy", "error": "Database not initialized"}
    
    try:
        # ✅ BEST PRACTICE: Use ping command for lightweight health check
        await _client.admin.command("ping")
        return {"status": "healthy", "database": settings.MONGODB_DATABASE}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def get_client() -> AsyncIOMotorClient:
    """
    Get the database client instance.
    
    ✅ USE CASE: When you need direct MongoDB operations outside of Beanie
    
    Raises:
        RuntimeError: If database is not initialized
    """
    if _client is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first."
        )
    return _client
