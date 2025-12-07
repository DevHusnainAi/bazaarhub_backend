"""
📋 SHARED PYDANTIC SCHEMAS
==========================

🎯 PURPOSE:
Common response models and schemas used across all microservices.

✅ BEST PRACTICES:
1. Consistent API response format across all services
2. Proper pagination support for list endpoints
3. Standardized error responses
4. Use Pydantic for automatic validation and serialization

❌ BAD PRACTICES:
- Different response formats per endpoint (confusing for frontend)
- No pagination (loading 10,000 products at once!)
- Exposing internal errors to users (security risk)
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    Standard API response wrapper.
    
    ✅ BEST PRACTICE: Consistent response format
    Makes it easy for frontend to handle all responses uniformly.
    """
    success: bool = True
    message: str = "OK"


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    ✅ BEST PRACTICE: Include enough info to debug, but not sensitive data
    """
    success: bool = False
    message: str
    error_code: str | None = None
    details: dict[str, Any] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated list response.
    
    ✅ BEST PRACTICE: Always paginate list endpoints
    
    Example response:
    {
        "items": [...],
        "total": 150,
        "page": 1,
        "page_size": 20,
        "pages": 8,
        "has_next": true,
        "has_prev": false
    }
    """
    items: list[T]
    total: int = Field(description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Has next page")
    has_prev: bool = Field(description="Has previous page")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """
        Factory method to create paginated response.
        
        ✅ USAGE:
            products = await Product.find().skip(skip).limit(limit).to_list()
            total = await Product.count()
            return PaginatedResponse.create(products, total, page, page_size)
        """
        pages = (total + page_size - 1) // page_size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )


class PaginationParams(BaseModel):
    """
    Query parameters for pagination.
    
    ✅ USE AS: Query dependency in routes
    
    Example:
        @router.get("/products")
        async def list_products(
            pagination: PaginationParams = Depends()
        ):
            ...
    """
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page (max 100)"
    )
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias for page_size for database query."""
        return self.page_size


class HealthResponse(BaseModel):
    """Health check response for monitoring."""
    status: str = "healthy"
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    dependencies: dict[str, dict] = Field(
        default_factory=dict,
        description="Health status of dependencies (db, redis, etc.)"
    )


class TimestampMixin(BaseModel):
    """
    Mixin for created_at and updated_at fields.
    
    ✅ BEST PRACTICE: Track when records are created/modified
    """
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
