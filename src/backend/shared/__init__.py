"""
🔧 SHARED MODULE
================

Shared utilities, configuration, and authentication for all microservices.
"""

from backend.shared.config import settings
from backend.shared.database import (
    check_database_health,
    close_database,
    get_client,
    init_database,
)
from backend.shared.logging import configure_logging, get_logger
from backend.shared.schemas import (
    BaseResponse,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    # Config
    "settings",
    # Database
    "init_database",
    "close_database",
    "get_client",
    "check_database_health",
    # Logging
    "configure_logging",
    "get_logger",
    # Schemas
    "BaseResponse",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
]
