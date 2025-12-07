"""
🛣️ ORDER SERVICE ROUTES
========================

API endpoints for order operations.
"""

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from backend.services.orders.models import (
    CreateOrderRequest,
    OrderListItem,
    OrderResponse,
    UpdateOrderStatusRequest,
)
from backend.services.orders.service import order_service
from backend.shared import PaginatedResponse, PaginationParams
from backend.shared.auth import CurrentUserId

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
)
async def create_order(
    user_id: CurrentUserId,
    data: CreateOrderRequest,
) -> OrderResponse:
    """
    Create a new order from the current user's cart.
    
    This will:
    1. Take items from the cart
    2. Create an order with shipping address
    3. Clear the cart
    """
    return await order_service.create_order(user_id, data)


@router.get(
    "",
    response_model=PaginatedResponse[OrderListItem],
    summary="List user's orders",
)
async def list_orders(
    user_id: CurrentUserId,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[OrderListItem]:
    """
    Get the current user's order history.
    
    Orders are sorted by date (newest first).
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return await order_service.list_orders(user_id, pagination)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
)
async def get_order(
    user_id: CurrentUserId,
    order_id: str,
) -> OrderResponse:
    """
    Get detailed information about a specific order.
    """
    return await order_service.get_order(user_id, order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status (admin)",
)
async def update_order_status(
    order_id: str,
    data: UpdateOrderStatusRequest,
) -> OrderResponse:
    """
    Update the status of an order.
    
    **Note**: This should be admin-only in production.
    """
    return await order_service.update_status(order_id, data.status)
