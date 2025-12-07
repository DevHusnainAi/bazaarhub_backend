"""
🚀 ORDER SERVICE - MAIN APPLICATION
====================================

FastAPI application entry point for the Order Service.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.orders.models import Order
from backend.services.orders.routes import router as order_router
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
    configure_logging()
    await init_database([Order])
    yield
    await close_database()


app = FastAPI(
    title="Order Service",
    description="Order management and checkout",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api/orders" if settings.ENVIRONMENT == "production" else "",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(order_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    db_health = await check_database_health()
    return HealthResponse(
        status="healthy" if db_health["status"] == "healthy" else "degraded",
        service="order-service",
        version=settings.APP_VERSION,
        timestamp=datetime.now(),
        dependencies={"mongodb": db_health},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.services.orders.main:app",
        host="0.0.0.0",
        port=settings.ORDER_SERVICE_PORT,
        reload=settings.DEBUG,
    )
