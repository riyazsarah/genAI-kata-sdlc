# Farm-to-Table Marketplace - Architecture Documentation

## Overview

The Farm-to-Table Marketplace is a full-stack web application built with **FastAPI** and **PostgreSQL** (via Supabase) that connects consumers directly with local farmers. The platform follows a **layered architecture pattern** with clear separation of concerns.

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Browser   │  │  Mobile App │  │  Admin UI   │  │  External Systems   │ │
│  │  (Jinja2)   │  │   (Future)  │  │  (Jinja2)   │  │   (API Consumers)   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         FastAPI Application                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │ │
│  │  │   /api/v1    │  │   /farmer    │  │    /shop     │  │   /admin   │  │ │
│  │  │   REST API   │  │    Pages     │  │    Pages     │  │   Pages    │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUSINESS LOGIC LAYER                               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐  │
│  │  AuthService   │ │ ProductService │ │ FarmerService  │ │ CartService  │  │
│  └────────────────┘ └────────────────┘ └────────────────┘ └──────────────┘  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                   │
│  │ ProfileService │ │  EmailService  │ │  OrderService  │                   │
│  └────────────────┘ └────────────────┘ └────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA ACCESS LAYER                                  │
│  ┌──────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │   UserRepo   │ │  ProductRepo   │ │   FarmerRepo   │ │    CartRepo    │  │
│  └──────────────┘ └────────────────┘ └────────────────┘ └────────────────┘  │
│  ┌──────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │  AddressRepo │ │ PaymentRepo    │ │   OrderRepo    │ │  ProfileRepo   │  │
│  └──────────────┘ └────────────────┘ └────────────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     Supabase (PostgreSQL)                               │ │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────────────┐  │ │
│  │  │  users  │ │ products │ │ farmers  │ │ orders │ │ shopping_carts  │  │ │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────┘ └─────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI 0.115.0+ |
| **Server** | Uvicorn 0.32.0+ |
| **Database** | Supabase (PostgreSQL) |
| **Authentication** | JWT (PyJWT) + bcrypt |
| **Encryption** | Cryptography (Fernet/AES-128) |
| **Templating** | Jinja2 |
| **Validation** | Pydantic v2 |
| **Frontend Enhancement** | HTMX |
| **Rate Limiting** | slowapi |
| **Email** | SMTP (Mock for development) |

## Project Structure

```
genAI-kata-sdlc/
├── app/
│   ├── api/v1/                 # API Routers
│   │   ├── router.py           # Main router aggregator
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── users.py            # User management
│   │   ├── farmers.py          # Farmer profile API
│   │   ├── products.py         # Product management API
│   │   ├── catalog.py          # Public product catalog
│   │   ├── cart.py             # Shopping cart API
│   │   ├── orders.py           # Order management
│   │   ├── wishlist.py         # Wishlist/favorites
│   │   ├── admin.py            # Admin operations
│   │   ├── farmer_pages.py     # Farmer HTML pages
│   │   ├── shop_pages.py       # Shop HTML pages
│   │   └── health.py           # Health checks
│   │
│   ├── core/                   # Core utilities
│   │   ├── config.py           # Application settings
│   │   ├── security.py         # Cryptographic functions
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── encryption.py       # Data encryption
│   │
│   ├── db/                     # Database
│   │   └── supabase.py         # Supabase client
│   │
│   ├── models/                 # Pydantic models
│   │   ├── user.py             # User models
│   │   ├── farmer.py           # Farmer models
│   │   ├── product.py          # Product models
│   │   ├── cart.py             # Cart models
│   │   ├── profile.py          # Profile models
│   │   └── ...
│   │
│   ├── repositories/           # Data access layer
│   │   ├── user.py             # User CRUD
│   │   ├── farmer.py           # Farmer CRUD
│   │   ├── product.py          # Product CRUD
│   │   ├── cart.py             # Cart operations
│   │   └── ...
│   │
│   ├── services/               # Business logic
│   │   ├── auth.py             # Authentication logic
│   │   ├── farmer.py           # Farmer operations
│   │   ├── product.py          # Product operations
│   │   ├── cart.py             # Cart operations
│   │   ├── email.py            # Email service
│   │   └── profile.py          # Profile operations
│   │
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html           # Base layout
│   │   ├── auth/               # Auth pages
│   │   ├── farmer/             # Farmer dashboard
│   │   ├── shop/               # Consumer shop
│   │   └── admin/              # Admin pages
│   │
│   ├── static/                 # Static assets
│   │   ├── css/
│   │   └── js/
│   │
│   └── main.py                 # Application entry point
│
├── migrations/                 # SQL migrations
├── tests/                      # Test suite
├── user_stories/               # Requirements (JSON)
├── run.py                      # Development server
└── pyproject.toml              # Dependencies
```

## Request Flow

```
┌──────────┐     ┌─────────┐     ┌─────────┐     ┌────────────┐     ┌──────────┐
│  Client  │────▶│  Router │────▶│ Service │────▶│ Repository │────▶│ Database │
└──────────┘     └─────────┘     └─────────┘     └────────────┘     └──────────┘
     │               │               │                │                   │
     │   HTTP Req    │   Validate    │   Business     │    SQL Query      │
     │   + Auth      │   + Route     │   Logic        │    + Model        │
     │               │               │                │    Mapping        │
     ◀───────────────┴───────────────┴────────────────┴───────────────────┘
              HTTP Response (JSON/HTML)
```

### Example: Product Creation Flow

```python
POST /api/v1/farmers/products
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. DEPENDENCY INJECTION                                          │
│    get_current_active_user() → Validates JWT token               │
│    get_product_service() → Creates service instance              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. REQUEST VALIDATION                                            │
│    Pydantic ProductCreate model validates input                  │
│    - name, category, price, unit, quantity                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BUSINESS LOGIC (ProductService)                               │
│    - Validate farmer ownership                                   │
│    - Apply business rules                                        │
│    - Calculate derived fields                                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. DATA ACCESS (ProductRepository)                               │
│    - Insert into 'products' table                                │
│    - Return created record                                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. RESPONSE                                                      │
│    ProductResponse model (excludes sensitive fields)             │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REGISTRATION FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User                    API                   Service              DB       │
│   │                       │                       │                  │       │
│   │  POST /auth/register  │                       │                  │       │
│   │──────────────────────▶│                       │                  │       │
│   │                       │  register_user()      │                  │       │
│   │                       │──────────────────────▶│                  │       │
│   │                       │                       │  email_exists()  │       │
│   │                       │                       │─────────────────▶│       │
│   │                       │                       │◀─────────────────│       │
│   │                       │                       │                  │       │
│   │                       │                       │  hash_password() │       │
│   │                       │                       │  gen_token()     │       │
│   │                       │                       │                  │       │
│   │                       │                       │  create_user()   │       │
│   │                       │                       │─────────────────▶│       │
│   │                       │                       │◀─────────────────│       │
│   │                       │                       │                  │       │
│   │                       │                       │  send_email()    │       │
│   │                       │◀──────────────────────│                  │       │
│   │  201 Created          │                       │                  │       │
│   │◀──────────────────────│                       │                  │       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOGIN FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User                    API                   Service              DB       │
│   │                       │                       │                  │       │
│   │  POST /auth/login     │                       │                  │       │
│   │──────────────────────▶│                       │                  │       │
│   │                       │  login_user()         │                  │       │
│   │                       │──────────────────────▶│                  │       │
│   │                       │                       │  get_by_email()  │       │
│   │                       │                       │─────────────────▶│       │
│   │                       │                       │◀─────────────────│       │
│   │                       │                       │                  │       │
│   │                       │                       │  check_lockout() │       │
│   │                       │                       │  verify_pass()   │       │
│   │                       │                       │  check_verified()│       │
│   │                       │                       │                  │       │
│   │                       │                       │  gen_tokens()    │       │
│   │                       │                       │  - access (30m)  │       │
│   │                       │                       │  - refresh (7d)  │       │
│   │                       │◀──────────────────────│                  │       │
│   │  { user, tokens }     │                       │                  │       │
│   │◀──────────────────────│                       │                  │       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema (ERD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTITY RELATIONSHIPS                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │    users     │
                              ├──────────────┤
                              │ id (PK)      │
                              │ email        │
                              │ password_hash│
                              │ full_name    │
                              │ phone        │
                              │ role         │
                              │ email_verified│
                              │ created_at   │
                              └──────┬───────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          │ 1:1                      │ 1:N                      │ 1:N
          ▼                          ▼                          ▼
   ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
   │   farmers    │          │user_addresses│          │shopping_carts│
   ├──────────────┤          ├──────────────┤          ├──────────────┤
   │ id (PK)      │          │ id (PK)      │          │ id (PK)      │
   │ user_id (FK) │          │ user_id (FK) │          │ user_id (FK) │
   │ farm_name    │          │ street       │          │ created_at   │
   │ farm_desc    │          │ city         │          └──────┬───────┘
   │ farm_address │          │ state        │                 │
   │ practices[]  │          │ zip_code     │                 │ 1:N
   │ completed    │          │ is_default   │                 ▼
   └──────┬───────┘          └──────────────┘          ┌──────────────┐
          │                                            │  cart_items  │
          │ 1:N                                        ├──────────────┤
          ▼                                            │ id (PK)      │
   ┌──────────────┐                                    │ cart_id (FK) │
   │   products   │◀───────────────────────────────────│ product_id   │
   ├──────────────┤                                    │ quantity     │
   │ id (PK)      │                                    │ unit_price   │
   │ farmer_id(FK)│                                    └──────────────┘
   │ name         │
   │ category     │     ┌──────────────┐
   │ description  │     │ farm_images  │
   │ price        │     ├──────────────┤
   │ unit         │     │ id (PK)      │
   │ quantity     │     │ farmer_id(FK)│◀────┐
   │ status       │     │ image_url    │     │
   │ images[]     │     │ caption      │     │
   │ seasonality[]│     │ is_primary   │     │ 1:N
   │ version      │     └──────────────┘     │
   └──────────────┘                          │
                         ┌──────────────┐    │
                         │ farm_videos  │    │
                         ├──────────────┤    │
                         │ id (PK)      │    │
                         │ farmer_id(FK)│◀───┤
                         │ video_url    │    │
                         │ platform     │    │
                         │ title        │    │
                         └──────────────┘    │
                                             │
                         ┌──────────────┐    │
                         │farmer_bank_  │    │
                         │accounts      │    │
                         ├──────────────┤    │
                         │ id (PK)      │    │
                         │ farmer_id(FK)│◀───┘
                         │ holder_name  │
                         │ acct_encrypted│
                         │ routing_enc  │
                         │ last_four    │
                         └──────────────┘
```

## API Endpoints Summary

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register consumer |
| POST | `/farmer/register` | Register farmer |
| POST | `/login` | User login |
| POST | `/verify-email` | Verify email |
| POST | `/forgot-password` | Request password reset |
| POST | `/reset-password` | Reset password |
| POST | `/refresh-token` | Refresh access token |

### Farmers (`/api/v1/farmers`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Get farmer profile |
| PUT | `/farm` | Update farm details |
| POST | `/farm/images` | Add farm image |
| DELETE | `/farm/images/{id}` | Delete farm image |
| POST | `/farm/videos` | Add farm video |
| DELETE | `/farm/videos/{id}` | Delete farm video |
| POST | `/bank-account` | Add/update bank account |

### Products (`/api/v1/farmers/products`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List farmer's products |
| POST | `/` | Create product |
| GET | `/{id}` | Get product details |
| PUT | `/{id}` | Update product |
| DELETE | `/{id}` | Delete product |
| PUT | `/{id}/inventory` | Update stock |
| PUT | `/{id}/price` | Update price |

### Catalog (`/api/v1/catalog`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | Browse products |
| GET | `/products/{id}` | Product details |
| GET | `/categories` | List categories |

### Cart (`/api/v1/cart`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get cart |
| POST | `/items` | Add to cart |
| PUT | `/items/{id}` | Update quantity |
| DELETE | `/items/{id}` | Remove item |
| DELETE | `/` | Clear cart |
| POST | `/checkout` | Process checkout |

## Security Implementation

### Password Security
- **Hashing:** bcrypt with auto-generated salt
- **Validation:** Min 8 chars, uppercase, lowercase, digit, special char
- **Storage:** Only hash stored, never plaintext

### JWT Authentication
- **Algorithm:** HS256
- **Access Token:** 30-minute expiry
- **Refresh Token:** 7-day expiry
- **Token Types:** Differentiated by `type` claim

### Account Protection
- **Lockout:** 5 failed attempts → 15-minute lockout
- **Email Verification:** Required before login
- **Token Expiry:** 24 hours for verification, 1 hour for password reset

### Data Encryption
- **Method:** Fernet (AES-128)
- **Usage:** Bank account numbers, routing numbers
- **Key Management:** Environment variable

## User Roles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER ROLES                                      │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│    Consumer     │     Farmer      │      Admin      │      Permissions      │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│       ✓         │        ✓        │        ✓        │ Browse products       │
│       ✓         │        ✓        │        ✓        │ View product details  │
│       ✓         │        ✓        │        ✓        │ Manage own profile    │
│       ✓         │        ✗        │        ✗        │ Add to cart           │
│       ✓         │        ✗        │        ✗        │ Place orders          │
│       ✓         │        ✗        │        ✗        │ Manage wishlist       │
│       ✗         │        ✓        │        ✗        │ Manage products       │
│       ✗         │        ✓        │        ✗        │ View own orders       │
│       ✗         │        ✓        │        ✗        │ Manage farm profile   │
│       ✗         │        ✓        │        ✗        │ Set up bank account   │
│       ✗         │        ✗        │        ✓        │ Manage all users      │
│       ✗         │        ✗        │        ✓        │ Moderate products     │
│       ✗         │        ✗        │        ✓        │ View platform stats   │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

## Design Patterns

| Pattern | Implementation |
|---------|----------------|
| **Repository** | Data access abstraction (`repositories/`) |
| **Service Layer** | Business logic encapsulation (`services/`) |
| **Dependency Injection** | FastAPI `Depends()` |
| **Factory** | Service creation via dependency functions |
| **Strategy** | Pluggable email services |
| **Singleton** | Cached settings and DB clients (`@lru_cache`) |
| **MVC** | Models + Routes + Services |

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=Farmary
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ENCRYPTION_KEY=your-fernet-key

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=xxx
SMTP_PASSWORD=xxx
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run python run.py

# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Type checking
uv run mypy .
```

## Deployment Considerations

### Production Checklist
- [ ] Change `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure production database credentials
- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set up production email service
- [ ] Enable database backups
- [ ] Configure logging and monitoring

### Scalability
- Stateless API design (JWT in requests)
- Database connection pooling via Supabase
- Horizontal scaling via load balancer
- Cached settings and clients

## Related Documentation

- [User Stories](/user_stories/) - Feature requirements
- [API Documentation](/docs) - Swagger UI (when running)
- [Database Migrations](/migrations/) - SQL schema changes
