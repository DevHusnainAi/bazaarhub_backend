
import asyncio
import os
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DATABASE", "ecommerce")

# Mock Data
CATEGORIES = [
    {"name": "Electronics", "image": "https://images.unsplash.com/photo-1498049860654-af1a5c5668ba?w=500&q=80"},
    {"name": "Fashion", "image": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=500&q=80"},
    {"name": "Home", "image": "https://images.unsplash.com/photo-1484101403633-562f891dc89a?w=500&q=80"},
    {"name": "Sports", "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&q=80"},
    {"name": "Beauty", "image": "https://images.unsplash.com/photo-1596462502278-27bfdd403cc2?w=500&q=80"},
]

PRODUCTS = [
    # Electronics
    {
        "name": "Wireless Noise Cancelling Headphones",
        "description": "Premium noise cancelling headphones with 30-hour battery life and crystal clear sound.",
        "price": 299.99,
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80",
        "stock": 50,
        "is_featured": True
    },
    {
        "name": "Smart Watch Series 7",
        "description": "Advanced health monitoring, fitness tracking, and seamless connectivity.",
        "price": 399.00,
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=500&q=80",
        "stock": 30,
        "is_featured": True
    },
    {
        "name": "4K Ultra HD Action Camera",
        "description": "Capture your adventures in stunning 4K resolution. Waterproof and durable.",
        "price": 149.50,
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&q=80",
        "stock": 100,
        "is_featured": False
    },
    {
        "name": "Bluetooth Portable Speaker",
        "description": "Powerful sound in a compact design. 12 hours of playtime.",
        "price": 59.99,
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500&q=80",
        "stock": 75,
        "is_featured": False
    },
    {
        "name": "Gaming Laptop Pro",
        "description": "High-performance gaming laptop with latest GPU and high refresh rate screen.",
        "price": 1299.00,
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&q=80",
        "stock": 10,
        "is_featured": True
    },
     {
        "name": "Professional DSLR Camera",
        "description": "Capture professional-quality photos and videos. Includes 18-55mm lens.",
        "price": 899.00,
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&q=80",
        "stock": 15,
        "is_featured": True
    },

    # Fashion
    {
        "name": "Classic Leather Jacket",
        "description": "Timeless leather jacket for a rugged look. Genuine leather.",
        "price": 199.99,
        "category": "Fashion",
        "image_url": "https://images.unsplash.com/photo-1551028919-ac7bcb7d7162?w=500&q=80",
        "stock": 20,
        "is_featured": True
    },
    {
        "name": "Slim Fit Denim Jeans",
        "description": "Comfortable and stylish slim fit jeans. Available in various sizes.",
        "price": 49.99,
        "category": "Fashion",
        "image_url": "https://images.unsplash.com/photo-1542272617-08f08637533d?w=500&q=80",
        "stock": 100,
        "is_featured": False
    },
    {
        "name": "Summer Floral Dress",
        "description": "Light and airy floral dress perfect for summer days.",
        "price": 35.00,
        "category": "Fashion",
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500&q=80",
        "stock": 50,
        "is_featured": False
    },
    {
        "name": "Running Sneakers",
        "description": "Lightweight and breathable running shoes for maximum comfort.",
        "price": 89.95,
        "category": "Fashion",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&q=80",
        "stock": 60,
        "is_featured": True
    },
    {
        "name": "Aviator Sunglasses",
        "description": "Classic aviator sunglasses with UV protection.",
        "price": 129.00,
        "category": "Fashion",
        "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=500&q=80",
        "stock": 40,
        "is_featured": False
    },
     {
        "name": "Designer Handbag",
        "description": "Elegant leather handbag for any occasion.",
        "price": 250.00,
        "category": "Fashion",
        "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500&q=80",
        "stock": 10,
        "is_featured": True
    },


    # Home
    {
        "name": "Modern Coffee Table",
        "description": "Minimalist coffee table to enhance your living room decor.",
        "price": 149.00,
        "category": "Home",
        "image_url": "https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=500&q=80",
        "stock": 15,
        "is_featured": False
    },
    {
        "name": "Soft Cotton Throw Blanket",
        "description": "Cozy and soft throw blanket for your sofa or bed.",
        "price": 29.99,
        "category": "Home",
        "image_url": "https://images.unsplash.com/photo-1580301762395-58079e563039?w=500&q=80",
        "stock": 80,
        "is_featured": False
    },
    {
        "name": "Ceramic Vase Set",
        "description": "Set of 3 ceramic vases in various sizes. Perfect for fresh flowers.",
        "price": 45.00,
        "category": "Home",
        "image_url": "https://images.unsplash.com/photo-1581783342308-f792ca11df53?w=500&q=80",
        "stock": 40,
        "is_featured": True
    },
    {
        "name": "Smart LED Bulb",
        "description": "Color-changing LED bulb controlled via smartphone app.",
        "price": 19.99,
        "category": "Home",
        "image_url": "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=500&q=80",
        "stock": 150,
        "is_featured": False
    },
    {
        "name": "Ergonomic Office Chair",
        "description": "Comfortable office chair with lumbar support for long work hours.",
        "price": 199.00,
        "category": "Home",
        "image_url": "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?w=500&q=80",
        "stock": 20,
        "is_featured": True
    },
    {
        "name": "Non-Stick Cookware Set",
        "description": "Complete set of non-stick pots and pans for your kitchen.",
        "price": 120.00,
        "category": "Home",
        "image_url": "https://images.unsplash.com/photo-1584269600519-112d071b35e6?w=500&q=80",
        "stock": 25,
        "is_featured": False
    },

    # Sports
    {
        "name": "Yoga Mat",
        "description": "Non-slip yoga mat for your daily practice. Eco-friendly material.",
        "price": 25.00,
        "category": "Sports",
        "image_url": "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=500&q=80",
        "stock": 60,
        "is_featured": False
    },
    {
        "name": "Adjustable Dumbbells",
        "description": "Space-saving adjustable dumbbells for home workouts.",
        "price": 199.00,
        "category": "Sports",
        "image_url": "https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?w=500&q=80",
        "stock": 10,
        "is_featured": True
    },
    {
        "name": "Tennis Racket",
        "description": "Professional tennis racket for power and control.",
        "price": 149.99,
        "category": "Sports",
        "image_url": "https://images.unsplash.com/photo-1617083934555-563d6412346b?w=500&q=80",
        "stock": 30,
        "is_featured": False
    },
    {
        "name": "Soccer Ball",
        "description": "Official size and weight soccer ball. Durable construction.",
        "price": 29.99,
        "category": "Sports",
        "image_url": "https://images.unsplash.com/photo-1614632537423-1e6c2e7e0aab?w=500&q=80",
        "stock": 100,
        "is_featured": False
    },
     {
        "name": "Hiking Backpack",
        "description": "Durable backpack for hiking and outdoor adventures.",
        "price": 89.99,
        "category": "Sports",
        "image_url": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=500&q=80",
        "stock": 40,
        "is_featured": True
    },
     {
        "name": "Cycling Helmet",
        "description": "Lightweight and safe helmet for cycling.",
        "price": 55.00,
        "category": "Sports",
        "image_url": "https://images.unsplash.com/photo-1557803175-2d854bea38b3?w=500&q=80",
        "stock": 50,
        "is_featured": False
    },


    # Beauty
    {
        "name": "Organic Face Serum",
        "description": "Rejuvenating face serum made with 100% organic ingredients.",
        "price": 45.00,
        "category": "Beauty",
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&q=80",
        "stock": 80,
        "is_featured": True
    },
    {
        "name": "Matte Lipstick Set",
        "description": "Set of 5 long-lasting matte lipsticks in vibrant shades.",
        "price": 35.00,
        "category": "Beauty",
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&q=80",
        "stock": 120,
        "is_featured": False
    },
    {
        "name": "Hair Dryer Professional",
        "description": "Ionic hair dryer for fast drying and reduced frizz.",
        "price": 79.99,
        "category": "Beauty",
        "image_url": "https://images.unsplash.com/photo-1522338140262-f46f5913618a?w=500&q=80",
        "stock": 40,
        "is_featured": False
    },
    {
        "name": "Perfume Elegance",
        "description": "Floral scent perfume for a touch of elegance.",
        "price": 85.00,
        "category": "Beauty",
        "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&q=80",
        "stock": 60,
        "is_featured": True
    },
    {
        "name": "Skincare Gift Set",
        "description": "Complete skincare routine in a beautiful gift box.",
        "price": 99.00,
        "category": "Beauty",
        "image_url": "https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?w=500&q=80",
        "stock": 30,
        "is_featured": True
    },
     {
        "name": "Makeup Brush Kit",
        "description": "Professional makeup brush set with synthetic bristles.",
        "price": 25.00,
        "category": "Beauty",
        "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdd403cc2?w=500&q=80",
        "stock": 100,
        "is_featured": False
    },
]

async def seed():
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Seed Categories
    print("Seeding Categories...")
    await db.categories.delete_many({}) # Clear existing
    
    category_map = {}
    for cat_data in CATEGORIES:
        result = await db.categories.insert_one(cat_data)
        category_map[cat_data["name"]] = str(result.inserted_id)
        print(f" - Added category: {cat_data['name']}")
        
    # 2. Seed Products
    print("\nSeeding Products...")
    await db.products.delete_many({}) # Clear existing
    
    for prod_data in PRODUCTS:
        # Generate some extra data
        prod_data["created_at"] = datetime.now()
        prod_data["updated_at"] = datetime.now()
        prod_data["slug"] = prod_data["name"].lower().replace(" ", "-")
        prod_data["price"] = str(prod_data["price"]) # Decimal as string for mongo
        prod_data["_class_id"] = "Product" # Beanie/ODM fields might exist, but plain insert is safer for now if not using ODM in script
        
        # We are using raw insert, so decimal handling might be tricky if backend expects Decimal128 or string
        # Looking at models.py: price: Annotated[Decimal, Field(ge=0, decimal_places=2)]
        # Beanie usually stores Decimal as Decimal128 in Mongo.
        # To be safe without Beanie dependency in script, let's use bson.Decimal128 if available or float if acceptable (model said avoid float but for seed script it might be ok if we convert back)
        # Actually, let's try to import Decimal128 from bson
        try:
             from bson.decimal128 import Decimal128
             prod_data["price"] = Decimal128(Decimal(prod_data["price"]))
        except ImportError:
             print("Warning: bson not found, using string for price")
             prod_data["price"] = str(prod_data["price"])

        
        await db.products.insert_one(prod_data)
        print(f" - Added product: {prod_data['name']}")
        
    print("\n✅ Seeding complete!")
    client.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
