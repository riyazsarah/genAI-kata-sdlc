"""Cart repository for database operations (US-013)."""

from decimal import Decimal
from uuid import UUID

from supabase import Client

from app.models.cart import CartInDB, CartItemInDB


class CartRepository:
    """Repository for shopping cart database operations."""

    CARTS_TABLE = "shopping_carts"
    ITEMS_TABLE = "cart_items"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    # ========================================================================
    # Cart Operations
    # ========================================================================

    def get_cart_by_user_id(self, user_id: UUID) -> CartInDB | None:
        """Get a user's shopping cart.

        Args:
            user_id: User's UUID.

        Returns:
            CartInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.CARTS_TABLE)
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return CartInDB(**response.data[0])
        return None

    def create_cart(self, user_id: UUID) -> CartInDB:
        """Create a new shopping cart for a user.

        Args:
            user_id: User's UUID.

        Returns:
            Created CartInDB.
        """
        response = (
            self.db.table(self.CARTS_TABLE)
            .insert({"user_id": str(user_id)})
            .execute()
        )

        return CartInDB(**response.data[0])

    def get_or_create_cart(self, user_id: UUID) -> CartInDB:
        """Get existing cart or create a new one for the user.

        Args:
            user_id: User's UUID.

        Returns:
            CartInDB instance.
        """
        cart = self.get_cart_by_user_id(user_id)
        if cart is None:
            cart = self.create_cart(user_id)
        return cart

    def delete_cart(self, cart_id: UUID) -> bool:
        """Delete a shopping cart and all its items.

        Args:
            cart_id: Cart's UUID.

        Returns:
            True if deleted, False otherwise.
        """
        response = (
            self.db.table(self.CARTS_TABLE)
            .delete()
            .eq("id", str(cart_id))
            .execute()
        )

        return len(response.data) > 0

    def update_cart_timestamp(self, cart_id: UUID) -> None:
        """Update cart's updated_at timestamp.

        Args:
            cart_id: Cart's UUID.
        """
        self.db.table(self.CARTS_TABLE).update(
            {"updated_at": "now()"}
        ).eq("id", str(cart_id)).execute()

    # ========================================================================
    # Cart Item Operations
    # ========================================================================

    def get_cart_items(self, cart_id: UUID) -> list[CartItemInDB]:
        """Get all items in a cart.

        Args:
            cart_id: Cart's UUID.

        Returns:
            List of CartItemInDB.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .select("*")
            .eq("cart_id", str(cart_id))
            .order("created_at", desc=False)
            .execute()
        )

        return [CartItemInDB(**item) for item in response.data]

    def get_cart_item(self, item_id: UUID) -> CartItemInDB | None:
        """Get a specific cart item by ID.

        Args:
            item_id: Cart item's UUID.

        Returns:
            CartItemInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .select("*")
            .eq("id", str(item_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return CartItemInDB(**response.data[0])
        return None

    def get_cart_item_by_product(
        self, cart_id: UUID, product_id: UUID
    ) -> CartItemInDB | None:
        """Get a cart item by product ID.

        Args:
            cart_id: Cart's UUID.
            product_id: Product's UUID.

        Returns:
            CartItemInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .select("*")
            .eq("cart_id", str(cart_id))
            .eq("product_id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return CartItemInDB(**response.data[0])
        return None

    def add_item(
        self,
        cart_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: Decimal,
    ) -> CartItemInDB:
        """Add an item to the cart.

        Args:
            cart_id: Cart's UUID.
            product_id: Product's UUID.
            quantity: Quantity to add.
            unit_price: Price per unit.

        Returns:
            Created CartItemInDB.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .insert({
                "cart_id": str(cart_id),
                "product_id": str(product_id),
                "quantity": quantity,
                "unit_price": float(unit_price),
            })
            .execute()
        )

        # Update cart timestamp
        self.update_cart_timestamp(cart_id)

        return CartItemInDB(**response.data[0])

    def update_item_quantity(
        self, item_id: UUID, quantity: int
    ) -> CartItemInDB | None:
        """Update a cart item's quantity.

        Args:
            item_id: Cart item's UUID.
            quantity: New quantity.

        Returns:
            Updated CartItemInDB if found, None otherwise.
        """
        # Get the item first to get cart_id for timestamp update
        item = self.get_cart_item(item_id)
        if item is None:
            return None

        response = (
            self.db.table(self.ITEMS_TABLE)
            .update({"quantity": quantity})
            .eq("id", str(item_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            # Update cart timestamp
            self.update_cart_timestamp(item.cart_id)
            return CartItemInDB(**response.data[0])
        return None

    def update_item_quantity_by_product(
        self, cart_id: UUID, product_id: UUID, quantity: int
    ) -> CartItemInDB | None:
        """Update a cart item's quantity by product ID.

        Args:
            cart_id: Cart's UUID.
            product_id: Product's UUID.
            quantity: New quantity.

        Returns:
            Updated CartItemInDB if found, None otherwise.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .update({"quantity": quantity})
            .eq("cart_id", str(cart_id))
            .eq("product_id", str(product_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            # Update cart timestamp
            self.update_cart_timestamp(cart_id)
            return CartItemInDB(**response.data[0])
        return None

    def remove_item(self, item_id: UUID) -> bool:
        """Remove an item from the cart.

        Args:
            item_id: Cart item's UUID.

        Returns:
            True if removed, False otherwise.
        """
        # Get the item first to get cart_id for timestamp update
        item = self.get_cart_item(item_id)
        if item is None:
            return False

        response = (
            self.db.table(self.ITEMS_TABLE)
            .delete()
            .eq("id", str(item_id))
            .execute()
        )

        if len(response.data) > 0:
            # Update cart timestamp
            self.update_cart_timestamp(item.cart_id)
            return True
        return False

    def clear_cart(self, cart_id: UUID) -> int:
        """Remove all items from a cart.

        Args:
            cart_id: Cart's UUID.

        Returns:
            Number of items removed.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .delete()
            .eq("cart_id", str(cart_id))
            .execute()
        )

        # Update cart timestamp
        self.update_cart_timestamp(cart_id)

        return len(response.data)

    def get_cart_item_count(self, cart_id: UUID) -> int:
        """Get the total number of items in a cart.

        Args:
            cart_id: Cart's UUID.

        Returns:
            Total quantity of all items.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .select("quantity")
            .eq("cart_id", str(cart_id))
            .execute()
        )

        return sum(item["quantity"] for item in response.data)

    def get_unique_item_count(self, cart_id: UUID) -> int:
        """Get the number of unique products in a cart.

        Args:
            cart_id: Cart's UUID.

        Returns:
            Number of unique products.
        """
        response = (
            self.db.table(self.ITEMS_TABLE)
            .select("id")
            .eq("cart_id", str(cart_id))
            .execute()
        )

        return len(response.data)
