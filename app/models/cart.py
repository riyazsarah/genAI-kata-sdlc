"""Cart models for shopping cart management (US-013)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Database Models
# ============================================================================


class CartInDB(BaseModel):
    """Database model for shopping cart."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartItemInDB(BaseModel):
    """Database model for cart item."""

    id: UUID
    cart_id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Request Models
# ============================================================================


class AddToCartRequest(BaseModel):
    """Request model for adding item to cart."""

    product_id: UUID = Field(..., description="Product ID to add to cart")
    quantity: int = Field(
        default=1,
        ge=1,
        le=999,
        description="Quantity to add (default 1)",
    )


class UpdateCartItemRequest(BaseModel):
    """Request model for updating cart item quantity."""

    quantity: int = Field(
        ...,
        ge=1,
        le=999,
        description="New quantity for the cart item",
    )


# ============================================================================
# Response Models
# ============================================================================


class CartItemProduct(BaseModel):
    """Product details embedded in cart item response."""

    id: UUID
    name: str
    category: str
    unit: str
    images: list[str] = []
    farmer_id: UUID
    farmer_name: str | None = None
    stock_quantity: int = 0
    status: str = "active"


class CartItemResponse(BaseModel):
    """Response model for a single cart item."""

    id: UUID
    product_id: UUID
    product: CartItemProduct
    quantity: int
    unit_price: Decimal
    subtotal: Decimal = Field(description="quantity * unit_price")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartSummary(BaseModel):
    """Summary of cart totals."""

    subtotal: Decimal = Field(description="Sum of all item subtotals")
    tax_rate: Decimal = Field(default=Decimal("0.08"), description="Tax rate (8%)")
    tax_amount: Decimal = Field(description="Calculated tax amount")
    total: Decimal = Field(description="Subtotal + tax")
    item_count: int = Field(description="Total number of items in cart")
    unique_items: int = Field(description="Number of unique products")


class CartResponse(BaseModel):
    """Response model for the full shopping cart."""

    id: UUID
    user_id: UUID
    items: list[CartItemResponse] = []
    summary: CartSummary
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmptyCartResponse(BaseModel):
    """Response model for an empty cart."""

    message: str = "Your cart is empty"
    item_count: int = 0


class CartOperationResponse(BaseModel):
    """Response model for cart operations (add/update/remove)."""

    success: bool
    message: str
    cart: CartResponse | None = None


class CartItemAddedResponse(BaseModel):
    """Response model when item is added to cart."""

    success: bool
    message: str
    item: CartItemResponse
    cart_summary: CartSummary
