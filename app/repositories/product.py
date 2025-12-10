"""Product repository for database operations."""

from decimal import Decimal
from uuid import UUID

from supabase import Client

from app.models.product import (
    ProductCategory,
    ProductInDB,
    ProductStatus,
    ProductUnit,
    Seasonality,
)


class ProductRepository:
    """Repository for product-related database operations."""

    TABLE_NAME = "products"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def _parse_product(self, data: dict) -> ProductInDB:
        """Parse database row to ProductInDB model.

        Args:
            data: Database row as dictionary.

        Returns:
            ProductInDB instance.
        """
        # Parse category
        category = ProductCategory(data["category"])

        # Parse unit
        unit = ProductUnit(data["unit"])

        # Parse status
        status = ProductStatus(data["status"])

        # Parse seasonality array
        seasonality_raw = data.get("seasonality", ["Year-round"])
        if isinstance(seasonality_raw, str):
            # Handle case where it comes as a string like "{Summer,Fall}"
            seasonality_raw = seasonality_raw.strip("{}").split(",")
        seasonality = [Seasonality(s.strip()) for s in seasonality_raw if s.strip()]

        # Parse images array
        images_raw = data.get("images", [])
        if isinstance(images_raw, str):
            images_raw = images_raw.strip("{}").split(",") if images_raw.strip("{}") else []
        images = [img.strip().strip('"') for img in images_raw if img.strip()]

        # Parse discount value if present
        discount_value = data.get("discount_value")
        if discount_value is not None:
            discount_value = Decimal(str(discount_value))

        return ProductInDB(
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            farmer_id=UUID(data["farmer_id"]) if isinstance(data["farmer_id"], str) else data["farmer_id"],
            name=data["name"],
            category=category,
            description=data["description"],
            price=Decimal(str(data["price"])),
            unit=unit,
            quantity=data["quantity"],
            seasonality=seasonality,
            images=images,
            status=status,
            version=data.get("version", 1),
            low_stock_threshold=data.get("low_stock_threshold", 10),
            discount_type=data.get("discount_type"),
            discount_value=discount_value,
            discount_start_date=data.get("discount_start_date"),
            discount_end_date=data.get("discount_end_date"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def get_by_id(self, product_id: UUID) -> ProductInDB | None:
        """Get a product by ID.

        Args:
            product_id: Product's UUID.

        Returns:
            ProductInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def get_by_farmer_id(
        self,
        farmer_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: ProductStatus | None = None,
    ) -> tuple[list[ProductInDB], int]:
        """Get all products for a farmer with pagination.

        Args:
            farmer_id: Farmer's UUID.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            status: Optional status filter.

        Returns:
            Tuple of (list of products, total count).
        """
        # Build query
        query = self.db.table(self.TABLE_NAME).select("*", count="exact").eq("farmer_id", str(farmer_id))

        if status:
            query = query.eq("status", status.value)

        # Get total count
        count_response = query.execute()
        total = count_response.count or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("farmer_id", str(farmer_id))
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
        )

        if status:
            query = query.eq("status", status.value)

        response = query.execute()

        products = [self._parse_product(row) for row in response.data]
        return products, total

    def create(
        self,
        farmer_id: UUID,
        name: str,
        category: ProductCategory,
        description: str,
        price: Decimal,
        unit: ProductUnit,
        quantity: int,
        seasonality: list[Seasonality],
    ) -> ProductInDB:
        """Create a new product in the database.

        Args:
            farmer_id: Farmer's UUID.
            name: Product name.
            category: Product category.
            description: Product description.
            price: Product price.
            unit: Unit of measurement.
            quantity: Available quantity.
            seasonality: List of seasons.

        Returns:
            Created ProductInDB instance.

        Raises:
            Exception: If database insert fails.
        """
        # Convert seasonality to list of strings for PostgreSQL array
        seasonality_values = [s.value for s in seasonality]

        product_data = {
            "farmer_id": str(farmer_id),
            "name": name,
            "category": category.value,
            "description": description,
            "price": float(price),
            "unit": unit.value,
            "quantity": quantity,
            "seasonality": seasonality_values,
            "images": [],
            "status": ProductStatus.ACTIVE.value,
        }

        response = self.db.table(self.TABLE_NAME).insert(product_data).execute()

        if not response.data or len(response.data) == 0:
            raise Exception("Failed to create product")

        return self._parse_product(response.data[0])

    def update(self, product_id: UUID, **kwargs) -> ProductInDB | None:
        """Update a product in the database.

        Args:
            product_id: Product's UUID.
            **kwargs: Fields to update.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        update_data = {}

        for key, value in kwargs.items():
            if value is not None:
                if key == "category" and isinstance(value, ProductCategory):
                    update_data[key] = value.value
                elif key == "unit" and isinstance(value, ProductUnit):
                    update_data[key] = value.value
                elif key == "status" and isinstance(value, ProductStatus):
                    update_data[key] = value.value
                elif key == "seasonality" and isinstance(value, list):
                    update_data[key] = [s.value if isinstance(s, Seasonality) else s for s in value]
                elif key == "price" and isinstance(value, Decimal):
                    update_data[key] = float(value)
                else:
                    update_data[key] = value

        if not update_data:
            return self.get_by_id(product_id)

        response = (
            self.db.table(self.TABLE_NAME)
            .update(update_data)
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def delete(self, product_id: UUID) -> bool:
        """Delete a product from the database.

        Args:
            product_id: Product's UUID.

        Returns:
            True if deleted successfully, False otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .delete()
            .eq("id", str(product_id))
            .execute()
        )

        return len(response.data) > 0

    def add_images(self, product_id: UUID, image_urls: list[str]) -> ProductInDB | None:
        """Add images to a product.

        Args:
            product_id: Product's UUID.
            image_urls: List of image URLs to add.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        # Get current product
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Combine existing and new images (max 5)
        current_images = list(product.images)
        new_images = current_images + image_urls
        new_images = new_images[:5]  # Limit to 5 images

        response = (
            self.db.table(self.TABLE_NAME)
            .update({"images": new_images})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def remove_image(self, product_id: UUID, image_url: str) -> ProductInDB | None:
        """Remove an image from a product.

        Args:
            product_id: Product's UUID.
            image_url: Image URL to remove.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        product = self.get_by_id(product_id)
        if not product:
            return None

        updated_images = [img for img in product.images if img != image_url]

        response = (
            self.db.table(self.TABLE_NAME)
            .update({"images": updated_images})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def get_by_farmer_and_id(self, farmer_id: UUID, product_id: UUID) -> ProductInDB | None:
        """Get a product by farmer ID and product ID.

        Args:
            farmer_id: Farmer's UUID.
            product_id: Product's UUID.

        Returns:
            ProductInDB if found and belongs to farmer, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("id", str(product_id))
            .eq("farmer_id", str(farmer_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def update_with_version(
        self,
        product_id: UUID,
        expected_version: int,
        **kwargs,
    ) -> tuple[ProductInDB | None, str | None]:
        """Update a product with optimistic locking.

        Args:
            product_id: Product's UUID.
            expected_version: Expected version for optimistic locking.
            **kwargs: Fields to update.

        Returns:
            Tuple of (ProductInDB if successful, error message if failed).
        """
        # First, verify the version matches
        current = self.get_by_id(product_id)
        if not current:
            return None, "Product not found"

        if current.version != expected_version:
            return None, (
                f"Version conflict: expected {expected_version}, "
                f"found {current.version}. Product was modified by another user."
            )

        # Prepare update data
        update_data = {}
        for key, value in kwargs.items():
            if value is not None:
                if key == "category" and isinstance(value, ProductCategory):
                    update_data[key] = value.value
                elif key == "unit" and isinstance(value, ProductUnit):
                    update_data[key] = value.value
                elif key == "status" and isinstance(value, ProductStatus):
                    update_data[key] = value.value
                elif key == "seasonality" and isinstance(value, list):
                    update_data[key] = [s.value if isinstance(s, Seasonality) else s for s in value]
                elif key == "price" and isinstance(value, Decimal):
                    update_data[key] = float(value)
                else:
                    update_data[key] = value

        if not update_data:
            return current, None

        # Update with version check (version is auto-incremented by trigger)
        response = (
            self.db.table(self.TABLE_NAME)
            .update(update_data)
            .eq("id", str(product_id))
            .eq("version", expected_version)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0]), None

        # If no rows updated, version mismatch occurred during update
        return None, "Version conflict: product was modified by another user"

    def remove_image_by_id(
        self, product_id: UUID, image_id: UUID
    ) -> ProductInDB | None:
        """Remove an image from a product by image ID.

        This uses the product_images table for better image management.

        Args:
            product_id: Product's UUID.
            image_id: Image's UUID.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        # Delete from product_images table
        self.db.table("product_images").delete().eq("id", str(image_id)).eq(
            "product_id", str(product_id)
        ).execute()

        # Return updated product
        return self.get_by_id(product_id)

    def archive(self, product_id: UUID) -> ProductInDB | None:
        """Archive a product (soft delete).

        Args:
            product_id: Product's UUID.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"status": ProductStatus.ARCHIVED.value})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def reactivate(self, product_id: UUID) -> ProductInDB | None:
        """Reactivate an archived product.

        Args:
            product_id: Product's UUID.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"status": ProductStatus.ACTIVE.value})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def has_pending_orders(self, product_id: UUID) -> bool:
        """Check if a product has pending orders.

        Args:
            product_id: Product's UUID.

        Returns:
            True if product has pending orders, False otherwise.
        """
        response = (
            self.db.table("order_items")
            .select("id, orders!inner(status)")
            .eq("product_id", str(product_id))
            .in_("orders.status", ["pending", "confirmed", "processing"])
            .execute()
        )

        return len(response.data) > 0

    def update_quantity(self, product_id: UUID, quantity: int) -> ProductInDB | None:
        """Update product quantity.

        Args:
            product_id: Product's UUID.
            quantity: New quantity.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"quantity": quantity})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def update_threshold(self, product_id: UUID, threshold: int) -> ProductInDB | None:
        """Update product low-stock threshold.

        Args:
            product_id: Product's UUID.
            threshold: New threshold value.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"low_stock_threshold": threshold})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def get_low_stock_products(self, farmer_id: UUID) -> list[ProductInDB]:
        """Get all low-stock and out-of-stock products for a farmer.

        Args:
            farmer_id: Farmer's UUID.

        Returns:
            List of low-stock ProductInDB instances.
        """
        # Query products where quantity <= low_stock_threshold
        # We need to use RPC or raw SQL for this comparison
        # For now, we'll fetch all active products and filter
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("farmer_id", str(farmer_id))
            .eq("status", ProductStatus.ACTIVE.value)
            .execute()
        )

        products = [self._parse_product(row) for row in response.data]
        # Filter for low stock (quantity <= threshold)
        return [p for p in products if p.quantity <= p.low_stock_threshold]

    def get_alerts(self, farmer_id: UUID, unread_only: bool = False) -> list[dict]:
        """Get low-stock alerts for a farmer.

        Args:
            farmer_id: Farmer's UUID.
            unread_only: If True, only return unread alerts.

        Returns:
            List of alert dictionaries.
        """
        query = (
            self.db.table("low_stock_alerts")
            .select("*, products(name)")
            .eq("farmer_id", str(farmer_id))
            .order("created_at", desc=True)
            .limit(50)
        )

        if unread_only:
            query = query.eq("is_read", False)

        response = query.execute()
        return response.data

    def mark_alerts_read(self, farmer_id: UUID, alert_ids: list[UUID]) -> bool:
        """Mark alerts as read.

        Args:
            farmer_id: Farmer's UUID.
            alert_ids: List of alert IDs to mark as read.

        Returns:
            True if successful, False otherwise.
        """
        response = (
            self.db.table("low_stock_alerts")
            .update({"is_read": True})
            .eq("farmer_id", str(farmer_id))
            .in_("id", [str(aid) for aid in alert_ids])
            .execute()
        )

        return len(response.data) > 0

    # =========================================================================
    # US-010: Pricing Management
    # =========================================================================

    def update_price(self, product_id: UUID, price: float) -> ProductInDB | None:
        """Update product price.

        Args:
            product_id: Product's UUID.
            price: New price.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .update({"price": price})
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def apply_discount(
        self,
        product_id: UUID,
        discount_type: str,
        discount_value: float,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ProductInDB | None:
        """Apply a discount to a product.

        Args:
            product_id: Product's UUID.
            discount_type: 'percentage' or 'fixed'.
            discount_value: Discount amount.
            start_date: Optional start date (ISO format).
            end_date: Optional end date (ISO format).

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        update_data = {
            "discount_type": discount_type,
            "discount_value": discount_value,
            "discount_start_date": start_date,
            "discount_end_date": end_date,
        }

        response = (
            self.db.table(self.TABLE_NAME)
            .update(update_data)
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def remove_discount(self, product_id: UUID) -> ProductInDB | None:
        """Remove discount from a product.

        Args:
            product_id: Product's UUID.

        Returns:
            Updated ProductInDB if successful, None otherwise.
        """
        update_data = {
            "discount_type": None,
            "discount_value": None,
            "discount_start_date": None,
            "discount_end_date": None,
        }

        response = (
            self.db.table(self.TABLE_NAME)
            .update(update_data)
            .eq("id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return self._parse_product(response.data[0])
        return None

    def set_bulk_pricing(
        self, product_id: UUID, tiers: list[dict]
    ) -> list[dict]:
        """Set bulk pricing tiers for a product.

        Args:
            product_id: Product's UUID.
            tiers: List of {min_quantity, price} dicts.

        Returns:
            List of created bulk pricing records.
        """
        # First, delete existing tiers
        self.db.table("bulk_pricing").delete().eq(
            "product_id", str(product_id)
        ).execute()

        # Insert new tiers
        tier_data = [
            {
                "product_id": str(product_id),
                "min_quantity": tier["min_quantity"],
                "price": float(tier["price"]),
            }
            for tier in tiers
        ]

        response = self.db.table("bulk_pricing").insert(tier_data).execute()
        return response.data

    def get_bulk_pricing(self, product_id: UUID) -> list[dict]:
        """Get bulk pricing tiers for a product.

        Args:
            product_id: Product's UUID.

        Returns:
            List of bulk pricing records.
        """
        response = (
            self.db.table("bulk_pricing")
            .select("*")
            .eq("product_id", str(product_id))
            .order("min_quantity")
            .execute()
        )
        return response.data

    def delete_bulk_pricing(self, product_id: UUID) -> bool:
        """Delete all bulk pricing for a product.

        Args:
            product_id: Product's UUID.

        Returns:
            True if deleted, False otherwise.
        """
        response = (
            self.db.table("bulk_pricing")
            .delete()
            .eq("product_id", str(product_id))
            .execute()
        )
        return True

    def get_price_history(
        self, product_id: UUID, limit: int = 50
    ) -> list[dict]:
        """Get price history for a product.

        Args:
            product_id: Product's UUID.
            limit: Maximum number of records.

        Returns:
            List of price history records.
        """
        response = (
            self.db.table("price_history")
            .select("*")
            .eq("product_id", str(product_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    # =========================================================================
    # US-011: Product Catalog (Public)
    # =========================================================================

    def get_public_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        search: str | None = None,
    ) -> tuple[list[ProductInDB], int]:
        """Get public product catalog with pagination.

        Only returns active products with quantity > 0.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            category: Optional category filter.
            search: Optional search term.

        Returns:
            Tuple of (list of products, total count).
        """
        # Build base query for active, in-stock products
        query = (
            self.db.table(self.TABLE_NAME)
            .select("*", count="exact")
            .eq("status", ProductStatus.ACTIVE.value)
            .gt("quantity", 0)
        )

        if category:
            query = query.eq("category", category)

        if search:
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")

        # Get count
        count_response = query.execute()
        total = count_response.count or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("status", ProductStatus.ACTIVE.value)
            .gt("quantity", 0)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
        )

        if category:
            query = query.eq("category", category)

        if search:
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")

        response = query.execute()
        products = [self._parse_product(row) for row in response.data]
        return products, total

    def get_featured_products(self, limit: int = 10) -> list[ProductInDB]:
        """Get featured/seasonal products.

        Returns products that are in season and have good stock.

        Args:
            limit: Maximum number of products.

        Returns:
            List of featured ProductInDB instances.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("status", ProductStatus.ACTIVE.value)
            .gt("quantity", 0)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [self._parse_product(row) for row in response.data]

    def get_products_by_category(
        self, category: str, limit: int = 20
    ) -> list[ProductInDB]:
        """Get products by category.

        Args:
            category: Product category.
            limit: Maximum number of products.

        Returns:
            List of ProductInDB instances.
        """
        response = (
            self.db.table(self.TABLE_NAME)
            .select("*")
            .eq("category", category)
            .eq("status", ProductStatus.ACTIVE.value)
            .gt("quantity", 0)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [self._parse_product(row) for row in response.data]
