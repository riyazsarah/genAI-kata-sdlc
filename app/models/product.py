"""Product-related Pydantic models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProductCategory(str, Enum):
    """Product category enumeration."""

    VEGETABLES = "Vegetables"
    FRUITS = "Fruits"
    DAIRY = "Dairy"
    MEAT = "Meat"
    EGGS = "Eggs"
    HONEY = "Honey"
    HERBS = "Herbs"
    GRAINS = "Grains"
    OTHER = "Other"


class ProductUnit(str, Enum):
    """Product unit enumeration."""

    LB = "lb"
    KG = "kg"
    EACH = "each"
    DOZEN = "dozen"
    BUNCH = "bunch"


class Seasonality(str, Enum):
    """Product seasonality enumeration."""

    SPRING = "Spring"
    SUMMER = "Summer"
    FALL = "Fall"
    WINTER = "Winter"
    YEAR_ROUND = "Year-round"


class ProductStatus(str, Enum):
    """Product status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProductCreate(BaseModel):
    """Request model for creating a product."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product name",
        examples=["Organic Tomatoes"],
    )
    category: ProductCategory = Field(
        ...,
        description="Product category",
        examples=[ProductCategory.VEGETABLES],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Product description",
        examples=["Fresh organic tomatoes grown without pesticides"],
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Product price",
        examples=[4.99],
    )
    unit: ProductUnit = Field(
        ...,
        description="Unit of measurement",
        examples=[ProductUnit.LB],
    )
    quantity: int = Field(
        ...,
        ge=0,
        description="Available quantity",
        examples=[100],
    )
    seasonality: list[Seasonality] = Field(
        default=[Seasonality.YEAR_ROUND],
        description="Seasonal availability",
        examples=[[Seasonality.SUMMER]],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean product name."""
        cleaned = " ".join(v.split())
        if len(cleaned) < 1:
            raise ValueError("Product name cannot be empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate and clean product description."""
        cleaned = v.strip()
        if len(cleaned) < 1:
            raise ValueError("Product description cannot be empty")
        return cleaned

    @field_validator("seasonality")
    @classmethod
    def validate_seasonality(cls, v: list[Seasonality]) -> list[Seasonality]:
        """Validate seasonality list."""
        if not v:
            return [Seasonality.YEAR_ROUND]
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for s in v:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique


class ProductUpdate(BaseModel):
    """Request model for updating a product."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Product name",
    )
    category: ProductCategory | None = Field(
        default=None,
        description="Product category",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
        description="Product description",
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        description="Product price",
    )
    unit: ProductUnit | None = Field(
        default=None,
        description="Unit of measurement",
    )
    quantity: int | None = Field(
        default=None,
        ge=0,
        description="Available quantity",
    )
    seasonality: list[Seasonality] | None = Field(
        default=None,
        description="Seasonal availability",
    )
    status: ProductStatus | None = Field(
        default=None,
        description="Product status",
    )
    version: int | None = Field(
        default=None,
        description="Current version for optimistic locking (required for updates)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate and clean product name."""
        if v is None:
            return None
        cleaned = " ".join(v.split())
        if len(cleaned) < 1:
            raise ValueError("Product name cannot be empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate and clean product description."""
        if v is None:
            return None
        cleaned = v.strip()
        if len(cleaned) < 1:
            raise ValueError("Product description cannot be empty")
        return cleaned


class StockStatus(str, Enum):
    """Stock status enumeration."""

    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class ProductInDB(BaseModel):
    """Product model as stored in the database."""

    id: UUID
    farmer_id: UUID
    name: str
    category: ProductCategory
    description: str
    price: Decimal
    unit: ProductUnit
    quantity: int
    seasonality: list[Seasonality]
    images: list[str] = []
    status: ProductStatus
    version: int = 1  # For optimistic locking
    low_stock_threshold: int = 10  # Threshold for low-stock alerts
    # Discount fields (US-010)
    discount_type: str | None = None
    discount_value: Decimal | None = None
    discount_start_date: datetime | None = None
    discount_end_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @property
    def stock_status(self) -> StockStatus:
        """Calculate stock status based on quantity and threshold."""
        if self.quantity == 0:
            return StockStatus.OUT_OF_STOCK
        elif self.quantity <= self.low_stock_threshold:
            return StockStatus.LOW_STOCK
        return StockStatus.IN_STOCK

    @property
    def has_active_discount(self) -> bool:
        """Check if product has an active discount."""
        if self.discount_type is None:
            return False
        now = datetime.now()
        if self.discount_start_date and self.discount_start_date > now:
            return False
        if self.discount_end_date and self.discount_end_date <= now:
            return False
        return True

    @property
    def effective_price(self) -> Decimal:
        """Calculate effective price after discount."""
        if not self.has_active_discount or self.discount_value is None:
            return self.price
        if self.discount_type == "percentage":
            return round(self.price * (1 - self.discount_value / 100), 2)
        elif self.discount_type == "fixed":
            return max(self.price - self.discount_value, Decimal("0.01"))
        return self.price


class ProductResponse(BaseModel):
    """Response model for product data."""

    id: UUID
    farmer_id: UUID
    farmer_name: str | None = None
    name: str
    category: ProductCategory
    description: str
    price: Decimal
    unit: ProductUnit
    quantity: int
    seasonality: list[Seasonality]
    images: list[str]
    status: ProductStatus
    version: int  # For optimistic locking - client should send this back on updates
    low_stock_threshold: int = 10
    stock_status: StockStatus | None = None  # Calculated field
    # Discount fields (US-010)
    discount_type: str | None = None
    discount_value: Decimal | None = None
    discount_start_date: datetime | None = None
    discount_end_date: datetime | None = None
    effective_price: Decimal | None = None  # Price after discount
    has_active_discount: bool = False
    # Bulk pricing indicator
    has_bulk_pricing: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Response model for paginated product list."""

    products: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoriesResponse(BaseModel):
    """Response model for product categories."""

    categories: list[dict[str, str]]


class ImageUploadResponse(BaseModel):
    """Response model for image upload."""

    message: str
    images: list[str]
    product_id: UUID


class InventoryUpdate(BaseModel):
    """Request model for updating product inventory."""

    quantity: int = Field(
        ...,
        ge=0,
        description="New quantity",
        examples=[50],
    )


class ThresholdUpdate(BaseModel):
    """Request model for updating low-stock threshold."""

    low_stock_threshold: int = Field(
        ...,
        ge=0,
        description="Low-stock threshold",
        examples=[10],
    )


class LowStockAlert(BaseModel):
    """Model for low-stock alert."""

    id: UUID
    product_id: UUID
    product_name: str
    previous_quantity: int
    current_quantity: int
    threshold: int
    alert_type: str  # 'low_stock', 'out_of_stock', 'back_in_stock'
    is_read: bool
    created_at: datetime


class LowStockProductResponse(BaseModel):
    """Response model for low-stock products."""

    id: UUID
    name: str
    category: ProductCategory
    quantity: int
    low_stock_threshold: int
    stock_status: StockStatus
    status: ProductStatus


# =============================================================================
# US-010: Pricing Management Models
# =============================================================================


class DiscountType(str, Enum):
    """Discount type enumeration."""

    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PriceUpdate(BaseModel):
    """Request model for updating product price."""

    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="New product price",
        examples=[5.99],
    )


class DiscountCreate(BaseModel):
    """Request model for applying a discount."""

    discount_type: DiscountType = Field(
        ...,
        description="Type of discount",
        examples=[DiscountType.PERCENTAGE],
    )
    discount_value: Decimal = Field(
        ...,
        gt=0,
        description="Discount value (percentage 0-100 or fixed amount)",
        examples=[20.0],
    )
    start_date: datetime | None = Field(
        default=None,
        description="When discount becomes active (NULL = immediately)",
    )
    end_date: datetime | None = Field(
        default=None,
        description="When discount expires (NULL = no expiry)",
    )

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: Decimal, info) -> Decimal:
        """Validate discount value based on type."""
        # Note: We can't access discount_type here in field_validator
        # Full validation happens in the service layer
        if v <= 0:
            raise ValueError("Discount value must be greater than 0")
        return v


class BulkPricingTier(BaseModel):
    """Model for a bulk pricing tier."""

    min_quantity: int = Field(
        ...,
        gt=0,
        description="Minimum quantity to qualify for this price",
        examples=[5],
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Price per unit at this quantity tier",
        examples=[4.50],
    )


class BulkPricingUpdate(BaseModel):
    """Request model for setting bulk pricing rules."""

    tiers: list[BulkPricingTier] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of bulk pricing tiers",
    )

    @field_validator("tiers")
    @classmethod
    def validate_tiers(cls, v: list[BulkPricingTier]) -> list[BulkPricingTier]:
        """Validate bulk pricing tiers."""
        if not v:
            raise ValueError("At least one pricing tier is required")
        # Sort by min_quantity
        sorted_tiers = sorted(v, key=lambda t: t.min_quantity)
        # Check for duplicate quantities
        quantities = [t.min_quantity for t in sorted_tiers]
        if len(quantities) != len(set(quantities)):
            raise ValueError("Duplicate quantity thresholds are not allowed")
        return sorted_tiers


class BulkPricingResponse(BaseModel):
    """Response model for bulk pricing."""

    id: UUID
    product_id: UUID
    min_quantity: int
    price: Decimal
    created_at: datetime
    updated_at: datetime


class PriceHistoryEntry(BaseModel):
    """Model for a price history entry."""

    id: UUID
    product_id: UUID
    previous_price: Decimal
    new_price: Decimal
    change_type: str
    changed_by: UUID | None
    change_reason: str | None
    created_at: datetime


class PriceHistoryResponse(BaseModel):
    """Response model for price history."""

    product_id: UUID
    entries: list[PriceHistoryEntry]
    total: int


class ProductWithPricing(BaseModel):
    """Product model with pricing information for consumers."""

    id: UUID
    farmer_id: UUID
    farmer_name: str | None = None
    name: str
    category: ProductCategory
    description: str
    price: Decimal  # Original price
    effective_price: Decimal  # Price after discount
    unit: ProductUnit
    quantity: int
    seasonality: list[Seasonality]
    images: list[str]
    status: ProductStatus
    stock_status: StockStatus | None = None
    # Discount info
    has_discount: bool = False
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    discount_end_date: datetime | None = None
    # Bulk pricing
    has_bulk_pricing: bool = False
    bulk_pricing_tiers: list[BulkPricingTier] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductCatalogResponse(BaseModel):
    """Response model for product catalog (consumer view)."""

    products: list[ProductWithPricing]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductDetailResponse(BaseModel):
    """Response model for product detail page (consumer view)."""

    product: ProductWithPricing
    related_products: list[ProductWithPricing] = []
