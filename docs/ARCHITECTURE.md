# 🏗️ Backend Architecture Overview

## Microservices Architecture

This e-commerce backend uses a **microservices architecture** with 4 independent services that communicate via HTTP.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Mobile App)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (Nginx :8000)                       │
│                                                                         │
│   /api/auth/*     →  Auth Service                                       │
│   /api/products/* →  Product Service                                    │
│   /api/cart/*     →  Cart Service                                       │
│   /api/orders/*   →  Order Service                                      │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                 │
         ▼                    ▼                    ▼                 ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐    ┌─────────────┐
│  Auth Svc   │      │ Product Svc │      │  Cart Svc   │    │ Order Svc   │
│   :8001     │      │    :8002    │      │    :8003    │    │    :8004    │
└─────────────┘      └─────────────┘      └─────────────┘    └─────────────┘
         │                    │                    │                 │
         └────────────────────┴────────────────────┴─────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │        MongoDB Atlas          │
                    │    (ecommerce database)       │
                    └───────────────────────────────┘
```

---

## Services Overview

| Service      | Port | Responsibility                      | Collections              |
| ------------ | ---- | ----------------------------------- | ------------------------ |
| **Auth**     | 8001 | User management, JWT tokens         | `users`                  |
| **Products** | 8002 | Product catalog, search, categories | `products`, `categories` |
| **Cart**     | 8003 | Shopping cart operations            | `carts`                  |
| **Orders**   | 8004 | Checkout, order history             | `orders`                 |

---

## Project Structure

```
backend/
├── src/backend/
│   ├── shared/                 # Shared code (all services use this)
│   │   ├── config.py           # Environment configuration
│   │   ├── database.py         # MongoDB connection
│   │   ├── schemas.py          # Common response models
│   │   ├── logging.py          # Structured logging
│   │   └── auth/
│   │       ├── jwt.py          # Token creation/validation
│   │       └── dependencies.py # FastAPI auth dependencies
│   │
│   └── services/
│       ├── auth/               # Auth Service
│       ├── products/           # Product Service
│       ├── cart/               # Cart Service
│       └── orders/             # Order Service
│
├── docker-compose.yml          # Local development
├── docker-compose.prod.yml     # Production
└── gateway/nginx.conf          # API Gateway config
```

---

## Shared Components

### Configuration (`shared/config.py`)

```python
# All services load settings from environment
from backend.shared import settings

settings.MONGODB_URI       # MongoDB connection string
settings.JWT_SECRET_KEY    # Secret for token signing
settings.CORS_ORIGINS      # Allowed origins
```

### Database (`shared/database.py`)

```python
# Initialize at service startup
await init_database([User])  # Pass models this service uses

# Health check
status = await check_database_health()
```

### Authentication (`shared/auth/`)

```python
# Create tokens
tokens = create_token_pair(user_id)

# Protect routes
@router.get("/profile")
async def profile(user_id: CurrentUserId):
    # user_id is validated from JWT
    pass
```

---

## Service Details

### 1️⃣ Auth Service (:8001)

**Purpose:** Handle user registration, login, and profile management.

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new user account |
| POST | `/auth/login` | Login, returns JWT tokens |
| POST | `/auth/refresh` | Get new access token |
| GET | `/auth/me` | Get current user profile |
| PATCH | `/auth/me` | Update profile |
| POST | `/auth/change-password` | Change password |

**Flow: Registration**

```
1. Client → POST /api/auth/register { email, password, name }
2. Auth Service:
   - Validates email is unique
   - Hashes password with bcrypt
   - Creates User document
   - Generates JWT tokens
3. Client ← { user, tokens: { access_token, refresh_token } }
```

**Flow: Login**

```
1. Client → POST /api/auth/login { email, password }
2. Auth Service:
   - Finds user by email
   - Verifies password hash
   - Updates last_login timestamp
   - Generates new JWT tokens
3. Client ← { user, tokens }
```

**Data Model:**

```javascript
// users collection
{
  _id: ObjectId,
  email: "user@example.com",     // Unique, indexed
  password_hash: "$2b$12$...",   // bcrypt
  name: "John Doe",
  is_active: true,
  created_at: ISODate,
  last_login: ISODate
}
```

---

### 2️⃣ Product Service (:8002)

**Purpose:** Manage product catalog with search and filtering.

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | List products (paginated, filterable) |
| GET | `/products/search?q=` | Full-text search |
| GET | `/products/featured` | Featured products |
| GET | `/products/{id}` | Single product details |
| POST | `/products` | Create product (admin) |
| PATCH | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Soft delete |
| GET | `/categories` | List all categories |

**Flow: Search Products**

```
1. Client → GET /api/products/search?q=headphones&page=1
2. Product Service:
   - Uses MongoDB text index on (name, description)
   - Applies pagination (skip, limit)
3. Client ← {
     items: [...],
     total: 45,
     page: 1,
     page_size: 20,
     has_next: true
   }
```

**Flow: Filter Products**

```
1. Client → GET /api/products?category=Electronics&min_price=50&max_price=200
2. Product Service:
   - Builds query with filters
   - Uses compound index on (category, price)
3. Client ← Paginated product list
```

**Data Model:**

```javascript
// products collection
{
  _id: ObjectId,
  name: "Wireless Headphones",
  description: "High-quality audio...",
  price: Decimal128("99.99"),
  category: "Electronics",
  tags: ["audio", "wireless"],
  image_url: "https://...",
  stock: 50,
  is_active: true,
  is_featured: true
}

// categories collection
{
  _id: ObjectId,
  name: "Electronics",
  parent_id: null,  // For nested categories
  sort_order: 1
}
```

---

### 3️⃣ Cart Service (:8003)

**Purpose:** Manage shopping carts (one per user).

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cart` | Get user's cart |
| POST | `/cart/items` | Add item to cart |
| PATCH | `/cart/items/{product_id}` | Update quantity |
| DELETE | `/cart/items/{product_id}` | Remove item |
| DELETE | `/cart` | Clear entire cart |

**Flow: Add to Cart**

```
1. Client → POST /api/cart/items { product_id, quantity: 2 }
   Headers: Authorization: Bearer <access_token>

2. Cart Service:
   a. Validates JWT token
   b. Calls Product Service to get product details
      → GET http://localhost:8002/products/{product_id}
   c. Gets or creates user's cart
   d. Adds/updates item in cart.items[]

3. Client ← {
     items: [
       { product_id, name, price, quantity, item_total }
     ],
     total_items: 5,
     subtotal: 199.98
   }
```

**Inter-Service Communication:**

```python
# Cart Service calls Product Service
async def _fetch_product(product_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8002/products/{product_id}"
        )
        return response.json()
```

**Data Model:**

```javascript
// carts collection
{
  _id: ObjectId,
  user_id: "user_123",        // One cart per user (unique index)
  items: [
    {
      product_id: "prod_abc",
      quantity: 2,
      name: "Headphones",     // Cached for display
      price: Decimal128("99.99"),
      image_url: "https://..."
    }
  ],
  updated_at: ISODate
}
```

---

### 4️⃣ Order Service (:8004)

**Purpose:** Handle checkout and order history.

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/orders` | Create order from cart |
| GET | `/orders` | List user's orders |
| GET | `/orders/{id}` | Order details |
| PATCH | `/orders/{id}/status` | Update status (admin) |

**Flow: Checkout**

```
1. Client → POST /api/orders
   {
     shipping_address: {
       full_name: "John Doe",
       address_line1: "123 Main St",
       city: "Karachi",
       postal_code: "75500",
       country: "PK",
       phone: "+92 300 1234567"
     }
   }

2. Order Service:
   a. Calls Cart Service to get cart
      → GET http://localhost:8003/cart
   b. Validates cart is not empty
   c. Creates Order with:
      - Snapshot of cart items (won't change if product price changes)
      - Calculates subtotal, tax (5%), total
      - Sets status: "pending"
   d. Calls Cart Service to clear cart
      → DELETE http://localhost:8003/cart

3. Client ← {
     id: "order_123",
     items: [...],
     subtotal: 199.98,
     tax: 10.00,
     total: 209.98,
     status: "pending"
   }
```

**Order Status Flow:**

```
pending → confirmed → processing → shipped → delivered
                  ↘ cancelled
```

**Data Model:**

```javascript
// orders collection
{
  _id: ObjectId,
  user_id: "user_123",
  items: [                    // Snapshot (prices frozen)
    {
      product_id: "prod_abc",
      name: "Headphones",
      price: Decimal128("99.99"),
      quantity: 2,
      item_total: Decimal128("199.98")
    }
  ],
  subtotal: Decimal128("199.98"),
  shipping_cost: Decimal128("0.00"),
  tax: Decimal128("10.00"),
  total: Decimal128("209.98"),
  shipping_address: { ... },
  status: "pending",
  created_at: ISODate
}
```

---

## Data Flow Diagrams

### Complete Purchase Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Mobile  │     │   Cart   │     │ Product  │     │  Order   │
│   App    │     │ Service  │     │ Service  │     │ Service  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. Add to Cart │                │                │
     │───────────────►│                │                │
     │                │ 2. Get product │                │
     │                │───────────────►│                │
     │                │◄───────────────│                │
     │                │ product details│                │
     │◄───────────────│                │                │
     │   cart updated │                │                │
     │                │                │                │
     │ 3. Checkout    │                │                │
     │────────────────┼────────────────┼───────────────►│
     │                │                │ 4. Get cart    │
     │                │◄───────────────┼────────────────│
     │                │────────────────┼───────────────►│
     │                │   cart items   │                │
     │                │                │ 5. Create order│
     │                │                │                │
     │                │ 6. Clear cart  │◄───────────────│
     │                │◄───────────────┼────────────────│
     │◄───────────────┼────────────────┼────────────────│
     │   order created│                │                │
```

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Mobile  │     │   Auth   │     │ MongoDB  │
│   App    │     │ Service  │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │ 1. Register    │                │
     │───────────────►│                │
     │                │ 2. Check email │
     │                │───────────────►│
     │                │◄───────────────│
     │                │ 3. Hash pass   │
     │                │ 4. Save user   │
     │                │───────────────►│
     │                │◄───────────────│
     │                │ 5. Generate JWT│
     │◄───────────────│                │
     │ { user, tokens}│                │
     │                │                │
     │ 6. API call    │                │
     │ (with token)   │                │
     │───────────────►│                │
     │                │ 7. Validate JWT│
     │                │ 8. Process req │
     │◄───────────────│                │
```

---

## Running the Services

### Local Development (without Docker)

```bash
cd backend

# Install dependencies
uv sync

# Copy and configure environment
copy .env.example .env
# Edit .env with your MongoDB Atlas URI

# Run each service in separate terminal
uv run uvicorn backend.services.auth.main:app --reload --port 8001
uv run uvicorn backend.services.products.main:app --reload --port 8002
uv run uvicorn backend.services.cart.main:app --reload --port 8003
uv run uvicorn backend.services.orders.main:app --reload --port 8004
```

### With Docker

```bash
cd backend

# Start all services + MongoDB + Redis
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### API Documentation

Each service has auto-generated Swagger docs:

- Auth: http://localhost:8001/docs
- Products: http://localhost:8002/docs
- Cart: http://localhost:8003/docs
- Orders: http://localhost:8004/docs

---

## Best Practices Implemented

| Practice               | Implementation                      |
| ---------------------- | ----------------------------------- |
| **12-Factor App**      | Config from environment             |
| **Health Checks**      | `/health` endpoint on each service  |
| **Structured Logging** | JSON logs with structlog            |
| **Graceful Shutdown**  | Lifespan context manager            |
| **CORS**               | Configured for mobile app           |
| **Password Security**  | bcrypt hashing                      |
| **JWT Tokens**         | Access (30min) + Refresh (7 days)   |
| **Pagination**         | All list endpoints paginated        |
| **Soft Delete**        | Products use `is_active` flag       |
| **Proper HTTP Codes**  | 201 Created, 401 Unauthorized, etc. |
