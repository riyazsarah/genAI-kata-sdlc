"""Product service for business logic operations."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.models.product import (
    ProductInDB,
    ProductResponse,
    ProductStatus,
    ProductUpdate,
)
from app.repositories.product import ProductRepository


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    success: bool
    error: str | None = None


@dataclass
class LowStockResult:
    """Result of a low-stock products query."""

    success: bool
    products: list[ProductResponse] | None = None
    error: str | None = None


@dataclass
class ProductResult:
    """Result of a product operation."""

    success: bool
    product: ProductResponse | None = None
    error: str | None = None


@dataclass
class ProductListResult:
    """Result of a product list operation."""

    success: bool
    products: list[ProductResponse] | None = None
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    error: str | None = None


class ProductService:
    """Service class for product-related business logic."""

    def __init__(self, product_repository: ProductRepository) -> None:
        """Initialize the service with a product repository.

        Args:
            product_repository: ProductRepository instance for data access.
        """
        self.product_repo = product_repository

    def _to_response(
        self, product: ProductInDB, include_bulk_pricing: bool = True
    ) -> ProductResponse:
        """Convert ProductInDB to ProductResponse.

        Args:
            product: ProductInDB instance.
            include_bulk_pricing: Whether to check for bulk pricing (default True).

        Returns:
            ProductResponse instance.
        """
        # Check if product has bulk pricing
        has_bulk_pricing = False
        if include_bulk_pricing:
            bulk_pricing = self.product_repo.get_bulk_pricing(product.id)
            has_bulk_pricing = len(bulk_pricing) > 0

        return ProductResponse(
            id=product.id,
            farmer_id=product.farmer_id,
            name=product.name,
            category=product.category,
            description=product.description,
            price=product.price,
            unit=product.unit,
            quantity=product.quantity,
            seasonality=product.seasonality,
            images=product.images,
            status=product.status,
            version=product.version,
            low_stock_threshold=product.low_stock_threshold,
            stock_status=product.stock_status,
            # Discount fields (US-010)
            discount_type=product.discount_type,
            discount_value=product.discount_value,
            discount_start_date=product.discount_start_date,
            discount_end_date=product.discount_end_date,
            effective_price=product.effective_price,
            has_active_discount=product.has_active_discount,
            has_bulk_pricing=has_bulk_pricing,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def get_product(self, farmer_id: UUID, product_id: UUID) -> ProductResult:
        """Get a product by ID for a specific farmer.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductResult with the product or error.
        """
        product = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)

        if not product:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to access it",
            )

        return ProductResult(success=True, product=self._to_response(product))

    def get_farmer_products(
        self,
        farmer_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: ProductStatus | None = None,
    ) -> ProductListResult:
        """Get all products for a farmer with pagination.

        Args:
            farmer_id: Farmer's UUID.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            status: Optional status filter.

        Returns:
            ProductListResult with paginated products.
        """
        products, total = self.product_repo.get_by_farmer_id(
            farmer_id, page, page_size, status
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return ProductListResult(
            success=True,
            products=[self._to_response(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_product(
        self,
        farmer_id: UUID,
        product_id: UUID,
        update_data: ProductUpdate,
    ) -> ProductResult:
        """Update a product with optimistic locking.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            update_data: ProductUpdate with fields to update.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Check if version is provided for optimistic locking
        if update_data.version is None:
            return ProductResult(
                success=False,
                error="Version is required for updates to prevent conflicts",
            )

        # Prepare update kwargs (exclude version as it's handled separately)
        update_kwargs = {}
        if update_data.name is not None:
            update_kwargs["name"] = update_data.name
        if update_data.category is not None:
            update_kwargs["category"] = update_data.category
        if update_data.description is not None:
            update_kwargs["description"] = update_data.description
        if update_data.price is not None:
            update_kwargs["price"] = update_data.price
        if update_data.unit is not None:
            update_kwargs["unit"] = update_data.unit
        if update_data.quantity is not None:
            update_kwargs["quantity"] = update_data.quantity
        if update_data.seasonality is not None:
            update_kwargs["seasonality"] = update_data.seasonality
        if update_data.status is not None:
            update_kwargs["status"] = update_data.status

        # Update with version check
        updated, error = self.product_repo.update_with_version(
            product_id=product_id,
            expected_version=update_data.version,
            **update_kwargs,
        )

        if error:
            return ProductResult(success=False, error=error)

        if not updated:
            return ProductResult(success=False, error="Failed to update product")

        return ProductResult(success=True, product=self._to_response(updated))

    def add_product_images(
        self,
        farmer_id: UUID,
        product_id: UUID,
        image_urls: list[str],
    ) -> ProductResult:
        """Add images to a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            image_urls: List of image URLs to add.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Check image limit (max 5)
        current_count = len(existing.images)
        if current_count + len(image_urls) > 5:
            return ProductResult(
                success=False,
                error=f"Cannot add {len(image_urls)} images. "
                f"Product already has {current_count} images (max 5)",
            )

        updated = self.product_repo.add_images(product_id, image_urls)
        if not updated:
            return ProductResult(success=False, error="Failed to add images")

        return ProductResult(success=True, product=self._to_response(updated))

    def remove_product_image(
        self,
        farmer_id: UUID,
        product_id: UUID,
        image_url: str,
    ) -> ProductResult:
        """Remove an image from a product by URL.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            image_url: Image URL to remove.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Check if image exists
        if image_url not in existing.images:
            return ProductResult(success=False, error="Image not found in product")

        updated = self.product_repo.remove_image(product_id, image_url)
        if not updated:
            return ProductResult(success=False, error="Failed to remove image")

        return ProductResult(success=True, product=self._to_response(updated))

    def remove_product_image_by_id(
        self,
        farmer_id: UUID,
        product_id: UUID,
        image_id: UUID,
    ) -> ProductResult:
        """Remove an image from a product by image ID.

        Uses the product_images table for better image management.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            image_id: Image's UUID.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        updated = self.product_repo.remove_image_by_id(product_id, image_id)
        if not updated:
            return ProductResult(success=False, error="Failed to remove image")

        return ProductResult(success=True, product=self._to_response(updated))

    # =========================================================================
    # US-008: Remove/Archive Product Listing
    # =========================================================================

    def delete_product(self, farmer_id: UUID, product_id: UUID) -> DeleteResult:
        """Permanently delete a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            DeleteResult indicating success or failure.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return DeleteResult(
                success=False,
                error="Product not found or you don't have permission to delete it",
            )

        # Check for pending orders
        if self.product_repo.has_pending_orders(product_id):
            return DeleteResult(
                success=False,
                error="Cannot delete product with pending orders. "
                "Please fulfill or cancel all orders first.",
            )

        # Delete the product
        deleted = self.product_repo.delete(product_id)
        if not deleted:
            return DeleteResult(success=False, error="Failed to delete product")

        return DeleteResult(success=True)

    def archive_product(self, farmer_id: UUID, product_id: UUID) -> ProductResult:
        """Archive a product (soft delete).

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductResult with archived product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to archive it",
            )

        # Check if already archived
        if existing.status == ProductStatus.ARCHIVED:
            return ProductResult(
                success=False,
                error="Product is already archived",
            )

        # Archive the product
        archived = self.product_repo.archive(product_id)
        if not archived:
            return ProductResult(success=False, error="Failed to archive product")

        return ProductResult(success=True, product=self._to_response(archived))

    def reactivate_product(self, farmer_id: UUID, product_id: UUID) -> ProductResult:
        """Reactivate an archived product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductResult with reactivated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to reactivate it",
            )

        # Check if product is archived
        if existing.status != ProductStatus.ARCHIVED:
            return ProductResult(
                success=False,
                error="Only archived products can be reactivated",
            )

        # Reactivate the product
        reactivated = self.product_repo.reactivate(product_id)
        if not reactivated:
            return ProductResult(success=False, error="Failed to reactivate product")

        return ProductResult(success=True, product=self._to_response(reactivated))

    # =========================================================================
    # US-009: Product Availability Management
    # =========================================================================

    def update_inventory(
        self, farmer_id: UUID, product_id: UUID, quantity: int
    ) -> ProductResult:
        """Update product inventory quantity.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            quantity: New quantity.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Update quantity
        updated = self.product_repo.update_quantity(product_id, quantity)
        if not updated:
            return ProductResult(success=False, error="Failed to update inventory")

        return ProductResult(success=True, product=self._to_response(updated))

    def update_threshold(
        self, farmer_id: UUID, product_id: UUID, threshold: int
    ) -> ProductResult:
        """Update product low-stock threshold.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            threshold: New threshold value.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Update threshold
        updated = self.product_repo.update_threshold(product_id, threshold)
        if not updated:
            return ProductResult(success=False, error="Failed to update threshold")

        return ProductResult(success=True, product=self._to_response(updated))

    def get_low_stock_products(self, farmer_id: UUID) -> LowStockResult:
        """Get all low-stock products for a farmer.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            LowStockResult with list of low-stock products.
        """
        products = self.product_repo.get_low_stock_products(farmer_id)

        return LowStockResult(
            success=True,
            products=[self._to_response(p) for p in products],
        )

    def mark_out_of_stock(self, farmer_id: UUID, product_id: UUID) -> ProductResult:
        """Mark a product as out of stock (set quantity to 0).

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductResult with updated product or error.
        """
        return self.update_inventory(farmer_id, product_id, 0)

    def mark_in_stock(
        self, farmer_id: UUID, product_id: UUID, quantity: int
    ) -> ProductResult:
        """Mark a product as in stock with given quantity.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            quantity: New quantity (must be > 0).

        Returns:
            ProductResult with updated product or error.
        """
        if quantity <= 0:
            return ProductResult(
                success=False,
                error="Quantity must be greater than 0 to mark as in-stock",
            )
        return self.update_inventory(farmer_id, product_id, quantity)

    # =========================================================================
    # US-010: Pricing Management
    # =========================================================================

    def update_price(
        self, farmer_id: UUID, product_id: UUID, price: Decimal
    ) -> ProductResult:
        """Update product price.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            price: New price.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        updated = self.product_repo.update_price(product_id, float(price))
        if not updated:
            return ProductResult(success=False, error="Failed to update price")

        return ProductResult(success=True, product=self._to_response(updated))

    def apply_discount(
        self,
        farmer_id: UUID,
        product_id: UUID,
        discount_type: str,
        discount_value: Decimal,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ProductResult:
        """Apply a discount to a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            discount_type: 'percentage' or 'fixed'.
            discount_value: Discount amount.
            start_date: Optional start date (ISO format).
            end_date: Optional end date (ISO format).

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Validate discount
        if discount_type == "percentage" and (discount_value <= 0 or discount_value > 100):
            return ProductResult(
                success=False,
                error="Percentage discount must be between 0 and 100",
            )

        if discount_type == "fixed" and discount_value >= existing.price:
            return ProductResult(
                success=False,
                error="Fixed discount cannot be greater than or equal to the product price",
            )

        updated = self.product_repo.apply_discount(
            product_id, discount_type, float(discount_value), start_date, end_date
        )
        if not updated:
            return ProductResult(success=False, error="Failed to apply discount")

        return ProductResult(success=True, product=self._to_response(updated))

    def remove_discount(self, farmer_id: UUID, product_id: UUID) -> ProductResult:
        """Remove discount from a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductResult with updated product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        if existing.discount_type is None:
            return ProductResult(
                success=False,
                error="Product does not have an active discount",
            )

        updated = self.product_repo.remove_discount(product_id)
        if not updated:
            return ProductResult(success=False, error="Failed to remove discount")

        return ProductResult(success=True, product=self._to_response(updated))

    def set_bulk_pricing(
        self, farmer_id: UUID, product_id: UUID, tiers: list[dict]
    ) -> ProductResult:
        """Set bulk pricing tiers for a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.
            tiers: List of {min_quantity, price} dicts.

        Returns:
            ProductResult with the product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        # Validate tiers - bulk prices should be less than regular price
        for tier in tiers:
            if Decimal(str(tier["price"])) >= existing.price:
                return ProductResult(
                    success=False,
                    error=f"Bulk price ₹{tier['price']} for {tier['min_quantity']}+ units "
                    f"must be less than regular price ₹{existing.price}",
                )

        self.product_repo.set_bulk_pricing(product_id, tiers)
        return ProductResult(success=True, product=self._to_response(existing))

    def get_bulk_pricing(self, farmer_id: UUID, product_id: UUID) -> list[dict]:
        """Get bulk pricing tiers for a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            List of bulk pricing tiers.
        """
        return self.product_repo.get_bulk_pricing(product_id)

    def delete_bulk_pricing(self, farmer_id: UUID, product_id: UUID) -> ProductResult:
        """Delete all bulk pricing for a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductResult with the product or error.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return ProductResult(
                success=False,
                error="Product not found or you don't have permission to update it",
            )

        self.product_repo.delete_bulk_pricing(product_id)
        return ProductResult(success=True, product=self._to_response(existing))

    def get_price_history(self, farmer_id: UUID, product_id: UUID) -> list[dict]:
        """Get price history for a product.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            List of price history entries.
        """
        # Verify product belongs to farmer
        existing = self.product_repo.get_by_farmer_and_id(farmer_id, product_id)
        if not existing:
            return []

        return self.product_repo.get_price_history(product_id)

    # =========================================================================
    # US-011: Public Product Catalog
    # =========================================================================

    def get_public_catalog(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        search: str | None = None,
    ) -> ProductListResult:
        """Get public product catalog with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.
            category: Optional category filter.
            search: Optional search term.

        Returns:
            ProductListResult with paginated products.
        """
        products, total = self.product_repo.get_public_products(
            page, page_size, category, search
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return ProductListResult(
            success=True,
            products=[self._to_response(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_featured_products(self, limit: int = 10) -> list[ProductResponse]:
        """Get featured products for homepage.

        Args:
            limit: Maximum number of products.

        Returns:
            List of ProductResponse instances.
        """
        products = self.product_repo.get_featured_products(limit)
        return [self._to_response(p) for p in products]

    def get_public_product(self, product_id: UUID) -> ProductResult:
        """Get a product for public viewing.

        Args:
            product_id: Product's UUID.

        Returns:
            ProductResult with product details.
        """
        product = self.product_repo.get_by_id(product_id)

        if not product:
            return ProductResult(success=False, error="Product not found")

        # Only return active products
        if product.status != ProductStatus.ACTIVE:
            return ProductResult(success=False, error="Product not available")

        return ProductResult(success=True, product=self._to_response(product))
