"""
🚀 AUTH SERVICE - MAIN APPLICATION
===================================

🎯 PURPOSE:
FastAPI application entry point for the Auth Service.

✅ BEST PRACTICES:
1. Configure CORS for mobile app access
2. Set up lifespan events for startup/shutdown
3. Include health check endpoint
4. Use proper exception handling

❌ BAD PRACTICES:
- No CORS config (mobile app can't access API)
- No graceful shutdown (connections leak)
- No health checks (K8s can't monitor service)
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.auth.models import User
from backend.services.auth.routes import router as auth_router
from backend.shared import (
    HealthResponse,
    check_database_health,
    close_database,
    configure_logging,
    init_database,
    settings,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    ✅ BEST PRACTICE: Use lifespan context manager (replaces on_event)
    - startup: Initialize connections
    - shutdown: Clean up resources
    """
    # === STARTUP ===
    configure_logging()
    
    # Initialize MongoDB with User model
    await init_database([User])
    
    yield  # App runs here
    
    # === SHUTDOWN ===
    await close_database()


# Create FastAPI application
app = FastAPI(
    title="Auth Service",
    description="User authentication and profile management",
    version="0.1.0",
    lifespan=lifespan,
    # ✅ BEST PRACTICE: Set root path for reverse proxy deployments
    root_path="/api/auth" if settings.ENVIRONMENT == "production" else "",
)


# ✅ BEST PRACTICE: Configure CORS for mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include auth routes
app.include_router(auth_router)


# ==================================================
# 🏥 HEALTH CHECK ENDPOINTS
# ==================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    ✅ USE CASE: Kubernetes liveness/readiness probes
    """
    db_health = await check_database_health()
    
    return HealthResponse(
        status="healthy" if db_health["status"] == "healthy" else "degraded",
        service="auth-service",
        version=settings.APP_VERSION,
        timestamp=datetime.now(),
        dependencies={"mongodb": db_health},
    )


# ==================================================
# 🏃 RUN CONFIGURATION
# ==================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.services.auth.main:app",
        host="0.0.0.0",
        port=settings.AUTH_SERVICE_PORT,
        reload=settings.DEBUG,
    )
