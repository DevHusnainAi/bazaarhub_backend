"""
📦 PRODUCT SERVICE (Business Logic)
====================================

🎯 PURPOSE:
Handle product CRUD, search, and caching operations.

✅ BEST PRACTICES:
1. Use MongoDB text search for full-text search
2. Cache frequently accessed data (Redis)
3. Implement proper pagination for large datasets
4. Use database indexes for filtered queries

❌ BAD PRACTICES:
- Loading all products at once (memory killer)
- No caching (slow repeated queries)
- Regex search instead of text index (inefficient)
"""

from decimal import Decimal

from beanie import PydanticObjectId
from beanie.operators import Text
from fastapi import HTTPException, status

from backend.services.products.models import (
    Category,
    CategoryResponse,
    Product,
    ProductCreate,
    ProductFilter,
    ProductListItem,
    ProductResponse,
    ProductUpdate,
)
from backend.shared import PaginatedResponse, PaginationParams
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class ProductService:
    """
    Product service handling CRUD and search operations.
    """
    
    # ==================================================
    # 📦 PRODUCT CRUD
    # ==================================================
    
    async def create_product(self, data: ProductCreate) -> ProductResponse:
        """
        Create a new product.
        
        Args:
            data: Product creation data
            
        Returns:
            Created product
        """
        logger.info("Creating product", name=data.name, category=data.category)
        
        product = Product(**data.model_dump())
        await product.insert()
        
        logger.info("Product created", product_id=str(product.id))
        return ProductResponse.from_document(product)
    
    async def get_product(self, product_id: str) -> ProductResponse:
        """
        Get a single product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product data
            
        Raises:
            HTTPException 404: If product not found
        """
        try:
            product = await Product.get(PydanticObjectId(product_id))
        except Exception:
            product = None
        
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        
        return ProductResponse.from_document(product)
    
    async def update_product(
        self,
        product_id: str,
        data: ProductUpdate,
    ) -> ProductResponse:
        """
        Update an existing product.
        
        Args:
            product_id: Product ID
            data: Fields to update
            
        Returns:
            Updated product
        """
        try:
            product = await Product.get(PydanticObjectId(product_id))
        except Exception:
            product = None
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        
        # ✅ BEST PRACTICE: Only update provided fields
        update_dict = data.model_dump(exclude_unset=True)
        
        if update_dict:
            for field, value in update_dict.items():
                setattr(product, field, value)
            product.update_timestamp()
            await product.save()
            
            logger.info(
                "Product updated",
                product_id=product_id,
                fields=list(update_dict.keys()),
            )
        
        return ProductResponse.from_document(product)
    
    async def delete_product(self, product_id: str) -> None:
        """
        Soft delete a product (set is_active=False).
        
        ✅ BEST PRACTICE: Soft delete preserves data
        """
        try:
            product = await Product.get(PydanticObjectId(product_id))
        except Exception:
            product = None
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        
        product.is_active = False
        product.update_timestamp()
        await product.save()
        
        logger.info("Product soft deleted", product_id=product_id)
    
    # ==================================================
    # 🔍 PRODUCT LISTING & SEARCH
    # ==================================================
    
    async def list_products(
        self,
        pagination: PaginationParams,
        filters: ProductFilter | None = None,
    ) -> PaginatedResponse[ProductListItem]:
        """
        List products with filtering and pagination.
        
        ✅ BEST PRACTICE: Always paginate list endpoints
        
        Args:
            pagination: Page number and size
            filters: Optional filters (category, price range, etc.)
            
        Returns:
            Paginated list of products
        """
        # Build query
        query = Product.find(Product.is_active == True)  # noqa: E712
        
        if filters:
            if filters.category:
                query = query.find(Product.category == filters.category)
            
            if filters.min_price is not None:
                query = query.find(Product.price >= filters.min_price)
            
            if filters.max_price is not None:
                query = query.find(Product.price <= filters.max_price)
            
            if filters.in_stock is True:
                query = query.find(Product.stock > 0)
            
            if filters.is_featured is not None:
                query = query.find(Product.is_featured == filters.is_featured)
        
        # Get total count
        total = await query.count()
        
        # Apply pagination and fetch
        products = await query.skip(pagination.skip).limit(pagination.limit).to_list()
        
        return PaginatedResponse.create(
            items=[ProductListItem.from_document(p) for p in products],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    async def search_products(
        self,
        search_query: str,
        pagination: PaginationParams,
    ) -> PaginatedResponse[ProductListItem]:
        """
        Full-text search on products.
        
        ✅ BEST PRACTICE: Use MongoDB text index for search
        This is much faster than regex matching.
        
        Args:
            search_query: Search text
            pagination: Page number and size
            
        Returns:
            Paginated search results
        """
        logger.info("Searching products", query=search_query)
        
        # ✅ Use MongoDB text search (requires text index)
        query = Product.find(
            Text(search_query),
            Product.is_active == True,  # noqa: E712
        )
        
        total = await query.count()
        products = await query.skip(pagination.skip).limit(pagination.limit).to_list()
        
        return PaginatedResponse.create(
            items=[ProductListItem.from_document(p) for p in products],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    async def get_featured_products(
        self,
        limit: int = 10,
    ) -> list[ProductListItem]:
        """
        Get featured products for homepage.
        
        Args:
            limit: Maximum number of products
            
        Returns:
            List of featured products
        """
        products = await Product.find(
            Product.is_active == True,  # noqa: E712
            Product.is_featured == True,  # noqa: E712
        ).limit(limit).to_list()
        
        return [ProductListItem.from_document(p) for p in products]
    
    # ==================================================
    # 📂 CATEGORIES
    # ==================================================
    
    async def list_categories(self) -> list[CategoryResponse]:
        """
        Get all active categories.
        
        Returns:
            List of categories
        """
        categories = await Category.find(
            Category.is_active == True  # noqa: E712
        ).sort(+Category.sort_order).to_list()
        
        return [CategoryResponse.from_document(c) for c in categories]
    
    async def get_products_by_category(
        self,
        category: str,
        pagination: PaginationParams,
    ) -> PaginatedResponse[ProductListItem]:
        """
        Get products in a specific category.
        
        Args:
            category: Category name
            pagination: Page number and size
            
        Returns:
            Paginated products in category
        """
        query = Product.find(
            Product.is_active == True,  # noqa: E712
            Product.category == category,
        )
        
        total = await query.count()
        products = await query.skip(pagination.skip).limit(pagination.limit).to_list()
        
        return PaginatedResponse.create(
            items=[ProductListItem.from_document(p) for p in products],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )


# Singleton instance
product_service = ProductService()
