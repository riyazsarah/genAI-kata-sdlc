"""Order repository for database operations."""

from decimal import Decimal
from uuid import UUID

from supabase import Client


class OrderRepository:
    """Repository for order database operations."""

    ORDERS_TABLE = "orders"
    ORDER_ITEMS_TABLE = "order_items"

    def __init__(self, db_client: Client) -> None:
        """Initialize the repository with a database client.

        Args:
            db_client: Supabase client instance.
        """
        self.db = db_client

    def create_order(
        self,
        user_id: UUID,
        total_amount: Decimal,
        status: str = "pending",
    ) -> dict | None:
        """Create a new order.

        Args:
            user_id: User's UUID.
            total_amount: Total order amount.
            status: Order status (default: pending).

        Returns:
            Created order dict if successful, None otherwise.
        """
        try:
            response = (
                self.db.table(self.ORDERS_TABLE)
                .insert({
                    "user_id": str(user_id),
                    "total_amount": float(total_amount),
                    "status": status,
                })
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception:
            return None

    def create_order_item(
        self,
        order_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: Decimal,
    ) -> dict | None:
        """Create an order item.

        Args:
            order_id: Order's UUID.
            product_id: Product's UUID.
            quantity: Quantity ordered.
            unit_price: Price per unit at time of order.

        Returns:
            Created order item dict if successful, None otherwise.
        """
        try:
            response = (
                self.db.table(self.ORDER_ITEMS_TABLE)
                .insert({
                    "order_id": str(order_id),
                    "product_id": str(product_id),
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                })
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception:
            return None

    def get_order_by_id(self, order_id: UUID) -> dict | None:
        """Get an order by ID.

        Args:
            order_id: Order's UUID.

        Returns:
            Order dict if found, None otherwise.
        """
        response = (
            self.db.table(self.ORDERS_TABLE)
            .select("*")
            .eq("id", str(order_id))
            .single()
            .execute()
        )

        return response.data if response.data else None

    def get_orders_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
    ) -> list[dict]:
        """Get all orders for a user.

        Args:
            user_id: User's UUID.
            status: Optional status filter.

        Returns:
            List of order dicts.
        """
        query = (
            self.db.table(self.ORDERS_TABLE)
            .select("*")
            .eq("user_id", str(user_id))
        )

        if status:
            query = query.eq("status", status)

        response = query.order("created_at", desc=True).execute()

        return response.data or []

    def get_order_items(self, order_id: UUID) -> list[dict]:
        """Get all items for an order.

        Args:
            order_id: Order's UUID.

        Returns:
            List of order item dicts.
        """
        response = (
            self.db.table(self.ORDER_ITEMS_TABLE)
            .select("*")
            .eq("order_id", str(order_id))
            .execute()
        )

        return response.data or []

    def update_order_status(
        self,
        order_id: UUID,
        status: str,
    ) -> dict | None:
        """Update an order's status.

        Args:
            order_id: Order's UUID.
            status: New status.

        Returns:
            Updated order dict if successful, None otherwise.
        """
        try:
            response = (
                self.db.table(self.ORDERS_TABLE)
                .update({"status": status})
                .eq("id", str(order_id))
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception:
            return None
