"""
📋 ORDER SERVICE (Business Logic)
==================================

Handle order creation, listing, and status updates.
"""

from decimal import Decimal

from beanie import PydanticObjectId
from fastapi import HTTPException, status
import httpx

from backend.services.orders.models import (
    CreateOrderRequest,
    Order,
    OrderItem,
    OrderListItem,
    OrderResponse,
    OrderStatus,
)
from backend.shared import PaginatedResponse, PaginationParams, settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class OrderService:
    """Order service handling order operations."""
    
    async def create_order(
        self,
        user_id: str,
        data: CreateOrderRequest,
    ) -> OrderResponse:
        """
        Create a new order from user's cart.
        
        Steps:
        1. Fetch cart from Cart Service
        2. Create order with cart items
        3. Clear the cart
        """
        logger.info("Creating order", user_id=user_id)
        
        # Fetch cart
        cart = await self._fetch_cart(user_id)
        
        if not cart.get("items"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty",
            )
        
        # Convert cart items to order items
        order_items = [
            OrderItem(
                product_id=item["product_id"],
                name=item["name"],
                price=Decimal(str(item["price"])),
                quantity=item["quantity"],
                item_total=Decimal(str(item["item_total"])),
            )
            for item in cart["items"]
        ]
        
        subtotal = Decimal(str(cart["subtotal"]))
        shipping_cost = Decimal("0.00")  # Free shipping for now
        tax = subtotal * Decimal("0.05")  # 5% tax
        total = subtotal + shipping_cost + tax
        
        # Create order
        order = Order(
            user_id=user_id,
            items=order_items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax.quantize(Decimal("0.01")),
            total=total.quantize(Decimal("0.01")),
            shipping_address=data.shipping_address,
            status=OrderStatus.PENDING,
        )
        await order.insert()
        
        # Clear cart after successful order
        await self._clear_cart(user_id)
        
        logger.info("Order created", order_id=str(order.id), total=str(total))
        return OrderResponse.from_document(order)
    
    async def get_order(self, user_id: str, order_id: str) -> OrderResponse:
        """Get a single order by ID."""
        try:
            order = await Order.get(PydanticObjectId(order_id))
        except Exception:
            order = None
        
        if not order or order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        
        return OrderResponse.from_document(order)
    
    async def list_orders(
        self,
        user_id: str,
        pagination: PaginationParams,
    ) -> PaginatedResponse[OrderListItem]:
        """List user's orders with pagination."""
        query = Order.find(Order.user_id == user_id).sort(-Order.created_at)
        
        total = await query.count()
        orders = await query.skip(pagination.skip).limit(pagination.limit).to_list()
        
        return PaginatedResponse.create(
            items=[OrderListItem.from_document(o) for o in orders],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    async def update_status(
        self,
        order_id: str,
        new_status: OrderStatus,
    ) -> OrderResponse:
        """Update order status (admin function)."""
        try:
            order = await Order.get(PydanticObjectId(order_id))
        except Exception:
            order = None
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        
        order.status = new_status
        order.update_timestamp()
        await order.save()
        
        logger.info("Order status updated", order_id=order_id, status=new_status)
        return OrderResponse.from_document(order)
    
    async def _fetch_cart(self, user_id: str) -> dict:
        """Fetch cart from Cart Service."""
        try:
            async with httpx.AsyncClient() as client:
                # Note: In production, use internal service URL
                response = await client.get(
                    f"http://localhost:{settings.CART_SERVICE_PORT}/cart",
                    headers={"Authorization": f"Bearer {user_id}"},  # Simplified
                    timeout=5.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error("Cart service unavailable", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cart service unavailable",
            )
    
    async def _clear_cart(self, user_id: str) -> None:
        """Clear cart after order creation."""
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"http://localhost:{settings.CART_SERVICE_PORT}/cart",
                    headers={"Authorization": f"Bearer {user_id}"},
                    timeout=5.0,
                )
        except httpx.RequestError as e:
            logger.warning("Failed to clear cart", error=str(e))


# Singleton instance
order_service = OrderService()
