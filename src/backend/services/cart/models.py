"""
🛒 CART MODEL (Cart Service)
============================

🎯 PURPOSE:
MongoDB document model for shopping carts.

✅ BEST PRACTICES:
1. One cart per user (upsert pattern)
2. Store minimal product info in cart items
3. Validate quantity limits
4. Calculate totals on the fly (prices may change)

❌ BAD PRACTICES:
- Multiple carts per user (inconsistent state)
- Storing full product data (stale data)
- Caching cart totals (outdated when prices change)
"""

from datetime import datetime
from decimal import Decimal

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """
    Single item in a cart.
    
    ✅ BEST PRACTICE: Store only product_id, fetch product details when needed
    This ensures prices are always current.
    """
    product_id: str
    quantity: int = Field(ge=1, le=99)
    
    # Cached product info (for display, not for pricing)
    name: str
    price: Decimal
    image_url: str


class Cart(Document):
    """
    Shopping cart document.
    
    ✅ COLLECTION: carts
    ✅ INDEX: user_id (unique - one cart per user)
    """
    user_id: Indexed(str, unique=True)  # type: ignore
    items: list[CartItem] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "carts"
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    @property
    def total_items(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate cart subtotal."""
        return sum(item.price * item.quantity for item in self.items)


# ==================================================
# 📤 RESPONSE SCHEMAS
# ==================================================

class CartItemResponse(BaseModel):
    """Cart item in API response."""
    product_id: str
    name: str
    price: Decimal
    image_url: str
    quantity: int
    item_total: Decimal


class CartResponse(BaseModel):
    """Cart data returned in API responses."""
    id: str
    items: list[CartItemResponse]
    total_items: int
    subtotal: Decimal
    updated_at: datetime
    
    @classmethod
    def from_document(cls, cart: Cart) -> "CartResponse":
        """Create response from Cart document."""
        items = [
            CartItemResponse(
                product_id=item.product_id,
                name=item.name,
                price=item.price,
                image_url=item.image_url,
                quantity=item.quantity,
                item_total=item.price * item.quantity,
            )
            for item in cart.items
        ]
        
        return cls(
            id=str(cart.id),
            items=items,
            total_items=cart.total_items,
            subtotal=cart.subtotal,
            updated_at=cart.updated_at,
        )


# ==================================================
# 📥 REQUEST SCHEMAS
# ==================================================

class AddToCartRequest(BaseModel):
    """Request to add item to cart."""
    product_id: str
    quantity: int = Field(ge=1, le=99, default=1)


class UpdateCartItemRequest(BaseModel):
    """Request to update item quantity."""
    quantity: int = Field(ge=1, le=99)
