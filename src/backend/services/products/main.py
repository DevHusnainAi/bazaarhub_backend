"""
🚀 PRODUCT SERVICE - MAIN APPLICATION
======================================

FastAPI application entry point for the Product Service.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.products.models import Category, Product
from backend.services.products.routes import category_router, router as product_router
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
    """Application lifespan manager."""
    # === STARTUP ===
    configure_logging()
    
    # Initialize MongoDB with Product and Category models
    await init_database([Product, Category])
    
    yield  # App runs here
    
    # === SHUTDOWN ===
    await close_database()


# Create FastAPI application
app = FastAPI(
    title="Product Service",
    description="Product catalog, search, and category management",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api/products" if settings.ENVIRONMENT == "production" else "",
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(product_router)
app.include_router(category_router)


# ==================================================
# 🏥 HEALTH CHECK
# ==================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring."""
    db_health = await check_database_health()
    
    return HealthResponse(
        status="healthy" if db_health["status"] == "healthy" else "degraded",
        service="product-service",
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
        "backend.services.products.main:app",
        host="0.0.0.0",
        port=settings.PRODUCT_SERVICE_PORT,
        reload=settings.DEBUG,
    )
