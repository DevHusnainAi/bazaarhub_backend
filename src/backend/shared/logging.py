"""
📝 STRUCTURED LOGGING MODULE
============================

🎯 PURPOSE:
Production-ready structured logging that outputs JSON in production
and human-readable logs in development.

✅ BEST PRACTICES:
1. Structured logs (JSON) for cloud environments (easy to parse)
2. Human-readable logs for local development
3. Include request context (request_id, user_id, etc.)
4. Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)

❌ BAD PRACTICES:
- Using print() statements (not captured by log collectors)
- Logging sensitive data (passwords, tokens, PII)
- Inconsistent log formats (hard to search/analyze)
- logging everything at DEBUG level (log noise)

📚 LOG LEVELS:
- DEBUG: Detailed info for debugging (not in production)
- INFO: General operational messages
- WARNING: Something unexpected but handled
- ERROR: Something failed but app continues
- CRITICAL: App is about to crash
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from backend.shared.config import settings


def configure_logging() -> None:
    """
    Configure structured logging for the application.
    
    ✅ CALL THIS: At application startup
    
    Example:
        from backend.shared.logging import configure_logging
        
        @app.on_event("startup")
        async def startup():
            configure_logging()
    """
    
    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,  # Include context vars
        structlog.stdlib.add_log_level,           # Add log level
        structlog.stdlib.add_logger_name,         # Add logger name
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),  # ISO timestamp
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.DEBUG:
        # ✅ DEVELOPMENT: Human-readable, colorful output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # ✅ PRODUCTION: JSON output for log aggregators
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance.
    
    ✅ USAGE:
        from backend.shared.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("Processing order", order_id="123", user_id="456")
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables that will be included in all logs.
    
    ✅ USE CASE: Add request_id at the start of each request
    
    Example:
        @app.middleware("http")
        async def add_request_id(request, call_next):
            request_id = str(uuid.uuid4())
            bind_context(request_id=request_id)
            response = await call_next(request)
            clear_context()
            return response
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
