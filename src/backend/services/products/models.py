"""
📦 PRODUCT MODEL (Product Service)
==================================

🎯 PURPOSE:
MongoDB document model for products with full-text search support.

✅ BEST PRACTICES:
1. Text indexes for search functionality (name, description)
2. Compound indexes for category + price filtering
3. Proper decimal handling for prices
4. Soft delete support (is_active flag)

❌ BAD PRACTICES:
- No indexes (slow queries with millions of products)
- Using float for prices (precision issues: 0.1 + 0.2 = 0.30000000000000004)
- Hard delete (lose data, can't recover)

📚 MONGODB INDEXES:
- Text index: Enables $text search on multiple fields
- Compound index: Optimizes queries that filter multiple fields
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class Product(Document):
    """
    Product document stored in MongoDB.
    
    ✅ COLLECTION: products
    ✅ INDEXES: 
        - Text index on (name, description) for search
        - Compound index on (category, price) for filtering
        - Index on is_active for filtering active products
    """
    # Basic info
    name: Indexed(str)  # type: ignore
    description: str
    
    # ✅ BEST PRACTICE: Use Decimal for money (avoid float precision issues)
    # Stored as string in MongoDB, validated as Decimal by Pydantic
    price: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    
    # Categorization
    category: Indexed(str)  # type: ignore
    tags: list[str] = Field(default_factory=list)
    
    # Images
    image_url: str
    images: list[str] = Field(default_factory=list)
    
    # Inventory
    stock: int = Field(ge=0, default=0)
    sku: str | None = None  # Stock Keeping Unit
    
    # Status
    is_active: Indexed(bool) = True  # type: ignore  # Soft delete support
    is_featured: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "products"
        # ✅ BEST PRACTICE: Define indexes for common queries
        indexes = [
            # Text index for full-text search
            [
                ("name", "text"),
                ("description", "text"),
            ],
        ]
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


class Category(Document):
    """
    Product category document.
    
    ✅ USE CASE: Organize products and enable category browsing
    """
    name: Indexed(str, unique=True)  # type: ignore
    description: str | None = None
    image_url: str | None = None
    parent_id: str | None = None  # For nested categories
    is_active: bool = True
    sort_order: int = 0
    
    class Settings:
        name = "categories"


# ==================================================
# 📤 RESPONSE SCHEMAS
# ==================================================

class ProductResponse(BaseModel):
    """Product data returned in API responses."""
    id: str
    name: str
    description: str
    price: Decimal
    category: str
    tags: list[str]
    image_url: str
    images: list[str]
    stock: int
    is_featured: bool
    created_at: datetime
    
    @classmethod
    def from_document(cls, product: Product) -> "ProductResponse":
        """Create response from Product document."""
        return cls(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            tags=product.tags,
            image_url=product.image_url,
            images=product.images,
            stock=product.stock,
            is_featured=product.is_featured,
            created_at=product.created_at,
        )


class ProductListItem(BaseModel):
    """Lightweight product for list views (less data to transfer)."""
    id: str
    name: str
    price: Decimal
    category: str
    image_url: str
    stock: int
    is_featured: bool
    
    @classmethod
    def from_document(cls, product: Product) -> "ProductListItem":
        """Create list item from Product document."""
        return cls(
            id=str(product.id),
            name=product.name,
            price=product.price,
            category=product.category,
            image_url=product.image_url,
            stock=product.stock,
            is_featured=product.is_featured,
        )


class CategoryResponse(BaseModel):
    """Category data for API responses."""
    id: str
    name: str
    description: str | None
    image_url: str | None
    parent_id: str | None
    
    @classmethod
    def from_document(cls, category: Category) -> "CategoryResponse":
        return cls(
            id=str(category.id),
            name=category.name,
            description=category.description,
            image_url=category.image_url,
            parent_id=category.parent_id,
        )


# ==================================================
# 📥 REQUEST SCHEMAS
# ==================================================

class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    price: Decimal = Field(ge=0, decimal_places=2)
    category: str
    tags: list[str] = Field(default_factory=list)
    image_url: str
    images: list[str] = Field(default_factory=list)
    stock: int = Field(ge=0, default=0)
    sku: str | None = None
    is_featured: bool = False


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    category: str | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    images: list[str] | None = None
    stock: int | None = Field(default=None, ge=0)
    is_featured: bool | None = None


class ProductFilter(BaseModel):
    """
    Query parameters for filtering products.
    
    ✅ BEST PRACTICE: Dedicated filter model for complex queries
    """
    category: str | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    in_stock: bool | None = None
    is_featured: bool | None = None
    search: str | None = Field(default=None, min_length=1)
