"""
🛣️ CART SERVICE ROUTES
=======================

API endpoints for shopping cart operations.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

from backend.services.cart.models import (
    AddToCartRequest,
    CartResponse,
    UpdateCartItemRequest,
)
from backend.services.cart.service import cart_service
from backend.shared.auth import CurrentUserId

router = APIRouter(prefix="/cart", tags=["Cart"])


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


@router.get(
    "",
    response_model=CartResponse,
    summary="Get current user's cart",
)
async def get_cart(user_id: CurrentUserId) -> CartResponse:
    """
    Get the current user's shopping cart.
    
    Creates an empty cart if none exists.
    """
    return await cart_service.get_cart(user_id)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
)
async def add_to_cart(
    user_id: CurrentUserId,
    data: AddToCartRequest,
) -> CartResponse:
    """
    Add a product to the cart.
    
    If the product is already in the cart, the quantity is increased.
    """
    return await cart_service.add_item(user_id, data)


@router.patch(
    "/items/{product_id}",
    response_model=CartResponse,
    summary="Update item quantity",
)
async def update_cart_item(
    user_id: CurrentUserId,
    product_id: str,
    data: UpdateCartItemRequest,
) -> CartResponse:
    """
    Update the quantity of an item in the cart.
    """
    return await cart_service.update_item(user_id, product_id, data)


@router.delete(
    "/items/{product_id}",
    response_model=CartResponse,
    summary="Remove item from cart",
)
async def remove_cart_item(
    user_id: CurrentUserId,
    product_id: str,
) -> CartResponse:
    """
    Remove a product from the cart.
    """
    return await cart_service.remove_item(user_id, product_id)


@router.delete(
    "",
    response_model=CartResponse,
    summary="Clear cart",
)
async def clear_cart(user_id: CurrentUserId) -> CartResponse:
    """
    Remove all items from the cart.
    """
    return await cart_service.clear_cart(user_id)
