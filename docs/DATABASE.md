# 🗃️ Database Documentation

## Overview

This e-commerce backend uses **MongoDB** as the database. If you're coming from **PostgreSQL**, here's a quick comparison:

| PostgreSQL  | MongoDB            | Description                        |
| ----------- | ------------------ | ---------------------------------- |
| Database    | Database           | Same concept                       |
| Table       | Collection         | Where data is stored               |
| Row         | Document           | A single record                    |
| Column      | Field              | A data attribute                   |
| Primary Key | `_id`              | Unique identifier (auto-generated) |
| Foreign Key | Reference (by ID)  | Manual, not enforced               |
| JOIN        | Embedded or Lookup | Different approaches               |
| Schema      | Flexible           | No strict schema required          |

---

## Why MongoDB for E-commerce?

| Feature                         | PostgreSQL                           | MongoDB                 | Winner for E-commerce |
| ------------------------------- | ------------------------------------ | ----------------------- | --------------------- |
| **Flexible product attributes** | Requires JSON columns or many tables | Native nested documents | ✅ MongoDB            |
| **Horizontal scaling**          | Complex (sharding)                   | Built-in                | ✅ MongoDB            |
| **Cart/Order items**            | Separate table + JOINs               | Embedded arrays         | ✅ MongoDB            |
| **Transactions**                | Native ACID                          | Supported (since v4.0)  | Both                  |
| **Complex queries**             | Better with SQL                      | Aggregation framework   | PostgreSQL            |

---

## Collections (Tables in PostgreSQL terms)

We have **5 collections** in the `ecommerce` database:

```
ecommerce/
├── users          # User accounts
├── products       # Product catalog
├── categories     # Product categories
├── carts          # Shopping carts (1 per user)
└── orders         # Purchase history
```

---

## 1️⃣ Users Collection

**PostgreSQL equivalent:**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
```

**MongoDB document:**

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),  // Auto-generated
  "email": "user@example.com",                   // Indexed, unique
  "password_hash": "$2b$12$...",                 // bcrypt hashed
  "name": "John Doe",
  "avatar_url": null,
  "is_active": true,
  "is_verified": false,
  "created_at": ISODate("2024-12-07T00:00:00Z"),
  "last_login": ISODate("2024-12-07T12:00:00Z")
}
```

**Indexes:**

- `email` - Unique index (like PostgreSQL UNIQUE constraint)

---

## 2️⃣ Products Collection

**PostgreSQL equivalent:**

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags TEXT[],                         -- Array type
    image_url TEXT NOT NULL,
    images TEXT[],
    stock INTEGER DEFAULT 0,
    sku VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_search ON products USING GIN(to_tsvector('english', name || ' ' || description));
```

**MongoDB document:**

```javascript
{
  "_id": ObjectId("..."),
  "name": "Wireless Bluetooth Headphones",
  "description": "High-quality audio with noise cancellation...",
  "price": Decimal128("99.99"),          // Exact decimal (like PostgreSQL DECIMAL)
  "category": "Electronics",
  "tags": ["audio", "wireless", "bluetooth"],
  "image_url": "https://example.com/headphones.jpg",
  "images": ["url1", "url2", "url3"],
  "stock": 50,
  "sku": "WBH-001",
  "is_active": true,
  "is_featured": true,
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**Indexes:**

- `name` - Regular index for filtering
- `category` - Regular index for filtering
- `is_active` - For filtering active products
- `Text index` on (name, description) - For full-text search

---

## 3️⃣ Categories Collection

**PostgreSQL equivalent:**

```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    image_url TEXT,
    parent_id UUID REFERENCES categories(id),  -- Self-referencing FK
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);
```

**MongoDB document:**

```javascript
{
  "_id": ObjectId("..."),
  "name": "Electronics",           // Unique
  "description": "Electronic gadgets and devices",
  "image_url": "https://example.com/electronics.jpg",
  "parent_id": null,               // null = top-level category
  "is_active": true,
  "sort_order": 1
}
```

**Nested categories example:**

```
Electronics (parent_id: null)
├── Phones (parent_id: "electronics_id")
│   ├── Smartphones (parent_id: "phones_id")
│   └── Feature Phones (parent_id: "phones_id")
└── Audio (parent_id: "electronics_id")
    ├── Headphones (parent_id: "audio_id")
    └── Speakers (parent_id: "audio_id")
```

---

## 4️⃣ Carts Collection

**PostgreSQL equivalent (would need 2 tables):**

```sql
-- In PostgreSQL, you'd need a separate table for items
CREATE TABLE carts (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id),  -- 1 cart per user
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cart_items (
    id UUID PRIMARY KEY,
    cart_id UUID REFERENCES carts(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 99),
    -- Cached product info for display
    name VARCHAR(200),
    price DECIMAL(10, 2),
    image_url TEXT
);
```

**MongoDB document (embedded - no need for separate table):**

```javascript
{
  "_id": ObjectId("..."),
  "user_id": "507f1f77bcf86cd799439011",  // References users._id
  "items": [                               // Embedded array (no JOIN needed!)
    {
      "product_id": "prod_abc123",
      "quantity": 2,
      "name": "Wireless Headphones",       // Cached for display
      "price": Decimal128("99.99"),
      "image_url": "https://..."
    },
    {
      "product_id": "prod_xyz789",
      "quantity": 1,
      "name": "Phone Case",
      "price": Decimal128("19.99"),
      "image_url": "https://..."
    }
  ],
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**Key difference from PostgreSQL:**

- In PostgreSQL, you'd need to JOIN `carts` + `cart_items` + `products`
- In MongoDB, items are embedded → single query, no JOINs

---

## 5️⃣ Orders Collection

**PostgreSQL equivalent (would need 3 tables):**

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    subtotal DECIMAL(10, 2),
    shipping_cost DECIMAL(10, 2),
    tax DECIMAL(10, 2),
    total DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    product_id UUID,  -- NOT a FK (snapshot, not reference)
    name VARCHAR(200),
    price DECIMAL(10, 2),
    quantity INTEGER,
    item_total DECIMAL(10, 2)
);

CREATE TABLE shipping_addresses (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    full_name VARCHAR(100),
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(2),
    phone VARCHAR(20)
);
```

**MongoDB document (all in one):**

```javascript
{
  "_id": ObjectId("..."),
  "user_id": "507f1f77bcf86cd799439011",
  "items": [                              // Snapshot (won't change if product changes)
    {
      "product_id": "prod_abc123",
      "name": "Wireless Headphones",
      "price": Decimal128("99.99"),
      "quantity": 2,
      "item_total": Decimal128("199.98")
    }
  ],
  "subtotal": Decimal128("199.98"),
  "shipping_cost": Decimal128("0.00"),
  "tax": Decimal128("10.00"),
  "total": Decimal128("209.98"),
  "shipping_address": {                   // Embedded object (no separate table!)
    "full_name": "John Doe",
    "address_line1": "123 Main Street",
    "address_line2": null,
    "city": "Karachi",
    "state": "Sindh",
    "postal_code": "75500",
    "country": "PK",
    "phone": "+92 300 1234567"
  },
  "status": "pending",                    // pending → confirmed → shipped → delivered
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

---

## Relationships Diagram

```
┌─────────────┐         ┌─────────────┐
│   USERS     │         │ CATEGORIES  │
│─────────────│         │─────────────│
│ _id (PK)    │         │ _id (PK)    │
│ email       │         │ name        │
│ name        │         │ parent_id   │──┐ Self-reference
└──────┬──────┘         └──────┬──────┘  │ (for nested)
       │                       │         │
       │ 1:1                   │ 1:N     └─────────────┘
       │                       │
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│   CARTS     │         │  PRODUCTS   │
│─────────────│         │─────────────│
│ _id (PK)    │         │ _id (PK)    │
│ user_id(FK) │◄───────►│ category    │ (by name, not ID)
│ items[]     │         │ name        │
│   └─prod_id │─────────│ price       │
└─────────────┘         └─────────────┘
       │
       │ Cart → Order
       ▼ (checkout)
┌─────────────┐
│   ORDERS    │
│─────────────│
│ _id (PK)    │
│ user_id(FK) │ ────► References users._id
│ items[]     │       (snapshot, not live)
│ total       │
│ status      │
│ address{}   │       Embedded object
└─────────────┘
```

---

## Key Differences from PostgreSQL

| Concept              | PostgreSQL                         | MongoDB in Our App           |
| -------------------- | ---------------------------------- | ---------------------------- |
| **Cart items**       | Separate `cart_items` table + JOIN | Embedded in `carts.items[]`  |
| **Order items**      | Separate `order_items` table       | Embedded in `orders.items[]` |
| **Shipping address** | Separate table or JSON column      | Embedded object              |
| **Foreign keys**     | Enforced by DB                     | Manual (in application code) |
| **Transactions**     | Automatic                          | Explicit (when needed)       |
| **Full-text search** | `tsvector` + `tsquery`             | Native text index            |

---

## Common Queries Comparison

### Get user with their orders

**PostgreSQL:**

```sql
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.id = '...';
```

**MongoDB:**

```javascript
// Option 1: Separate queries (preferred in microservices)
const user = await User.findById(userId);
const orders = await Order.find({ user_id: userId });

// Option 2: Aggregation with $lookup (like SQL JOIN)
db.users.aggregate([
  { $match: { _id: ObjectId("...") } },
  {
    $lookup: {
      from: "orders",
      localField: "_id",
      foreignField: "user_id",
      as: "orders",
    },
  },
]);
```

### Search products

**PostgreSQL:**

```sql
SELECT * FROM products
WHERE to_tsvector('english', name || ' ' || description) @@ plainto_tsquery('headphones')
AND is_active = true;
```

**MongoDB:**

```javascript
db.products.find({
  $text: { $search: "headphones" },
  is_active: true,
});
```

---

## Summary

1. **MongoDB uses documents** instead of rows - more flexible for nested data
2. **No JOINs needed** for cart items, order items - they're embedded
3. **References exist** but aren't enforced by DB - handled in application code
4. **Full-text search** is built-in with text indexes
5. **Scaling is easier** - MongoDB handles sharding natively

This structure is optimized for **read-heavy e-commerce workloads** where:

- Products are browsed frequently
- Carts and orders contain embedded items
- Search needs to be fast
