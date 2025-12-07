"""
🛣️ PRODUCT SERVICE ROUTES
==========================

🎯 PURPOSE:
API endpoints for product operations.

✅ BEST PRACTICES:
1. Separate endpoints for list, search, and single item
2. Use query parameters for filtering
3. Return consistent response format
4. Document all endpoints for OpenAPI
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from backend.services.products.models import (
    CategoryResponse,
    ProductCreate,
    ProductFilter,
    ProductListItem,
    ProductResponse,
    ProductUpdate,
)
from backend.services.products.service import product_service
from backend.shared import PaginatedResponse, PaginationParams

# ✅ BEST PRACTICE: Prefix and tags for organization
router = APIRouter(prefix="/products", tags=["Products"])
category_router = APIRouter(prefix="/categories", tags=["Categories"])


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# ==================================================
# 📦 PRODUCT ENDPOINTS
# ==================================================

@router.get(
    "",
    response_model=PaginatedResponse[ProductListItem],
    summary="List all products",
)
async def list_products(
    # ✅ BEST PRACTICE: Use Depends() for query params model
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock: bool | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
) -> PaginatedResponse[ProductListItem]:
    """
    List products with optional filtering.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **category**: Filter by category name
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **in_stock**: Only show products in stock
    - **is_featured**: Only show featured products
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    filters = ProductFilter(
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        is_featured=is_featured,
    )
    
    return await product_service.list_products(pagination, filters)


@router.get(
    "/search",
    response_model=PaginatedResponse[ProductListItem],
    summary="Search products",
)
async def search_products(
    q: str = Query(min_length=1, description="Search query"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[ProductListItem]:
    """
    Full-text search on product name and description.
    
    Uses MongoDB text index for fast searching.
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return await product_service.search_products(q, pagination)


@router.get(
    "/featured",
    response_model=list[ProductListItem],
    summary="Get featured products",
)
async def get_featured_products(
    limit: int = Query(default=10, ge=1, le=50),
) -> list[ProductListItem]:
    """
    Get featured products for homepage display.
    """
    return await product_service.get_featured_products(limit)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product details",
)
async def get_product(product_id: str) -> ProductResponse:
    """
    Get detailed information about a single product.
    """
    return await product_service.get_product(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(data: ProductCreate) -> ProductResponse:
    """
    Create a new product.
    
    **Note**: In production, this should require admin authentication.
    """
    return await product_service.create_product(data)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
) -> ProductResponse:
    """
    Update an existing product.
    
    Only provided fields will be updated (partial update).
    """
    return await product_service.update_product(product_id, data)


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Delete a product",
)
async def delete_product(product_id: str) -> MessageResponse:
    """
    Soft delete a product (sets is_active=False).
    
    Product data is preserved but won't appear in listings.
    """
    await product_service.delete_product(product_id)
    return MessageResponse(message="Product deleted successfully")


# ==================================================
# 📂 CATEGORY ENDPOINTS
# ==================================================

@category_router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List all categories",
)
async def list_categories() -> list[CategoryResponse]:
    """
    Get all active product categories.
    """
    return await product_service.list_categories()


@category_router.get(
    "/{category}/products",
    response_model=PaginatedResponse[ProductListItem],
    summary="Get products by category",
)
async def get_products_by_category(
    category: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[ProductListItem]:
    """
    Get all products in a specific category.
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return await product_service.get_products_by_category(category, pagination)
