"""
📋 ORDER MODEL (Order Service)
==============================

MongoDB document model for orders.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """Single item in an order."""
    product_id: str
    name: str
    price: Decimal
    quantity: int
    item_total: Decimal


class ShippingAddress(BaseModel):
    """Shipping address for order."""
    full_name: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str = "PK"
    phone: str


class Order(Document):
    """
    Order document stored in MongoDB.
    
    ✅ COLLECTION: orders
    ✅ INDEXES: user_id, status, created_at
    """
    user_id: Indexed(str)  # type: ignore
    
    # Order items (snapshot at time of order)
    items: list[OrderItem]
    
    # Totals
    subtotal: Decimal
    shipping_cost: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    total: Decimal
    
    # Shipping
    shipping_address: ShippingAddress
    
    # Status
    status: Indexed(OrderStatus) = OrderStatus.PENDING  # type: ignore
    
    # Timestamps
    created_at: Indexed(datetime) = Field(default_factory=datetime.now)  # type: ignore
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "orders"
    
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now()


# ==================================================
# 📤 RESPONSE SCHEMAS
# ==================================================

class OrderResponse(BaseModel):
    """Order data for API responses."""
    id: str
    items: list[OrderItem]
    subtotal: Decimal
    shipping_cost: Decimal
    tax: Decimal
    total: Decimal
    shipping_address: ShippingAddress
    status: OrderStatus
    created_at: datetime
    
    @classmethod
    def from_document(cls, order: Order) -> "OrderResponse":
        return cls(
            id=str(order.id),
            items=order.items,
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            tax=order.tax,
            total=order.total,
            shipping_address=order.shipping_address,
            status=order.status,
            created_at=order.created_at,
        )


class OrderListItem(BaseModel):
    """Lightweight order for list views."""
    id: str
    total_items: int
    total: Decimal
    status: OrderStatus
    created_at: datetime
    
    @classmethod
    def from_document(cls, order: Order) -> "OrderListItem":
        return cls(
            id=str(order.id),
            total_items=sum(item.quantity for item in order.items),
            total=order.total,
            status=order.status,
            created_at=order.created_at,
        )


# ==================================================
# 📥 REQUEST SCHEMAS
# ==================================================

class OrderItemRequest(BaseModel):
    """Item in create order request."""
    product_id: str
    quantity: int


class CreateOrderRequest(BaseModel):
    """Request to create order from cart."""
    items: list[OrderItemRequest]
    shipping_address: ShippingAddress


class UpdateOrderStatusRequest(BaseModel):
    """Request to update order status (admin only)."""
    status: OrderStatus
