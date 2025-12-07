"""
🛒 CART SERVICE (Business Logic)
=================================

Handle shopping cart operations.
"""

from decimal import Decimal

from beanie import PydanticObjectId
from fastapi import HTTPException, status
import httpx

from backend.services.cart.models import (
    AddToCartRequest,
    Cart,
    CartItem,
    CartResponse,
    UpdateCartItemRequest,
)
from backend.shared import settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class CartService:
    """Cart service handling shopping cart operations."""
    
    async def get_cart(self, user_id: str) -> CartResponse:
        """
        Get or create user's cart.
        
        ✅ BEST PRACTICE: Upsert pattern - create if not exists
        """
        cart = await Cart.find_one(Cart.user_id == user_id)
        
        if not cart:
            # Create empty cart
            cart = Cart(user_id=user_id, items=[])
            await cart.insert()
        
        return CartResponse.from_document(cart)
    
    async def add_item(
        self,
        user_id: str,
        data: AddToCartRequest,
    ) -> CartResponse:
        """
        Add item to cart or update quantity if exists.
        
        Args:
            user_id: User's ID
            data: Product ID and quantity
            
        Returns:
            Updated cart
        """
        logger.info(
            "Adding to cart",
            user_id=user_id,
            product_id=data.product_id,
            quantity=data.quantity,
        )
        
        # Get or create cart
        cart = await Cart.find_one(Cart.user_id == user_id)
        if not cart:
            cart = Cart(user_id=user_id, items=[])
        
        # Fetch product details from Product Service
        product_data = await self._fetch_product(data.product_id)
        
        # Check if item already in cart
        existing_item = next(
            (item for item in cart.items if item.product_id == data.product_id),
            None,
        )
        
        if existing_item:
            # Update quantity
            existing_item.quantity = min(existing_item.quantity + data.quantity, 99)
        else:
            # Add new item
            cart.items.append(
                CartItem(
                    product_id=data.product_id,
                    quantity=data.quantity,
                    name=product_data["name"],
                    price=Decimal(str(product_data["price"])),
                    image_url=product_data["image_url"],
                )
            )
        
        cart.update_timestamp()
        await cart.save()
        
        logger.info("Item added to cart", user_id=user_id, cart_items=len(cart.items))
        return CartResponse.from_document(cart)
    
    async def update_item(
        self,
        user_id: str,
        product_id: str,
        data: UpdateCartItemRequest,
    ) -> CartResponse:
        """
        Update item quantity in cart.
        """
        cart = await Cart.find_one(Cart.user_id == user_id)
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found",
            )
        
        # Find item
        item = next(
            (item for item in cart.items if item.product_id == product_id),
            None,
        )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not in cart",
            )
        
        # Update quantity
        item.quantity = data.quantity
        cart.update_timestamp()
        await cart.save()
        
        return CartResponse.from_document(cart)
    
    async def remove_item(self, user_id: str, product_id: str) -> CartResponse:
        """
        Remove item from cart.
        """
        cart = await Cart.find_one(Cart.user_id == user_id)
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found",
            )
        
        # Remove item
        cart.items = [item for item in cart.items if item.product_id != product_id]
        cart.update_timestamp()
        await cart.save()
        
        logger.info("Item removed from cart", user_id=user_id, product_id=product_id)
        return CartResponse.from_document(cart)
    
    async def clear_cart(self, user_id: str) -> CartResponse:
        """
        Clear all items from cart.
        """
        cart = await Cart.find_one(Cart.user_id == user_id)
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found",
            )
        
        cart.items = []
        cart.update_timestamp()
        await cart.save()
        
        logger.info("Cart cleared", user_id=user_id)
        return CartResponse.from_document(cart)
    
    async def _fetch_product(self, product_id: str) -> dict:
        """
        Fetch product details from Product Service.
        
        ✅ BEST PRACTICE: Service-to-service call for current data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{settings.PRODUCT_SERVICE_PORT}/products/{product_id}",
                    timeout=5.0,
                )
                
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Product not found",
                    )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error("Product service unavailable", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service unavailable",
            )


# Singleton instance
cart_service = CartService()
