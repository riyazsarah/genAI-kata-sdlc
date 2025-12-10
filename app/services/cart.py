"""Cart service for shopping cart business logic (US-013)."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.models.cart import (
    AddToCartRequest,
    CartItemAddedResponse,
    CartItemProduct,
    CartItemResponse,
    CartOperationResponse,
    CartResponse,
    CartSummary,
    EmptyCartResponse,
    UpdateCartItemRequest,
)
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository


# Tax rate constant
TAX_RATE = Decimal("0.08")  # 8% tax


@dataclass
class CartServiceResult:
    """Generic result for cart service operations."""

    success: bool
    message: str
    data: dict | None = None


class CartService:
    """Service for shopping cart operations."""

    def __init__(
        self,
        cart_repository: CartRepository,
        product_repository: ProductRepository,
    ) -> None:
        """Initialize the cart service.

        Args:
            cart_repository: Repository for cart database operations.
            product_repository: Repository for product database operations.
        """
        self.cart_repo = cart_repository
        self.product_repo = product_repository

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _calculate_summary(
        self, items: list[CartItemResponse]
    ) -> CartSummary:
        """Calculate cart summary from items.

        Args:
            items: List of cart items.

        Returns:
            CartSummary with totals.
        """
        subtotal = sum(item.subtotal for item in items)
        tax_amount = subtotal * TAX_RATE
        total = subtotal + tax_amount
        item_count = sum(item.quantity for item in items)

        return CartSummary(
            subtotal=subtotal,
            tax_rate=TAX_RATE,
            tax_amount=tax_amount.quantize(Decimal("0.01")),
            total=total.quantize(Decimal("0.01")),
            item_count=item_count,
            unique_items=len(items),
        )

    def _build_cart_item_response(
        self, cart_item, product
    ) -> CartItemResponse:
        """Build a CartItemResponse from cart item and product.

        Args:
            cart_item: CartItemInDB instance.
            product: ProductInDB instance.

        Returns:
            CartItemResponse with product details.
        """
        product_info = CartItemProduct(
            id=product.id,
            name=product.name,
            category=product.category.value,
            unit=product.unit.value,
            images=list(product.images),
            farmer_id=product.farmer_id,
            farmer_name=None,  # Could be enriched with farmer lookup
            stock_quantity=product.quantity,
            status=product.status.value,
        )

        subtotal = cart_item.unit_price * cart_item.quantity

        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product=product_info,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            subtotal=subtotal,
            created_at=cart_item.created_at,
            updated_at=cart_item.updated_at,
        )

    # ========================================================================
    # Cart Operations
    # ========================================================================

    def get_cart(self, user_id: UUID) -> CartResponse | EmptyCartResponse:
        """Get user's shopping cart with all items and summary.

        Args:
            user_id: User's UUID.

        Returns:
            CartResponse with items or EmptyCartResponse if cart is empty.
        """
        # Get or create cart
        cart = self.cart_repo.get_or_create_cart(user_id)

        # Get cart items
        cart_items = self.cart_repo.get_cart_items(cart.id)

        if not cart_items:
            return EmptyCartResponse()

        # Build response items with product details
        response_items: list[CartItemResponse] = []
        for cart_item in cart_items:
            product = self.product_repo.get_by_id(cart_item.product_id)
            if product:
                response_items.append(
                    self._build_cart_item_response(cart_item, product)
                )

        if not response_items:
            return EmptyCartResponse()

        # Calculate summary
        summary = self._calculate_summary(response_items)

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=response_items,
            summary=summary,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    def add_to_cart(
        self, user_id: UUID, request: AddToCartRequest
    ) -> CartItemAddedResponse | CartOperationResponse:
        """Add a product to the user's cart.

        Args:
            user_id: User's UUID.
            request: Add to cart request with product_id and quantity.

        Returns:
            CartItemAddedResponse on success, CartOperationResponse on failure.
        """
        # Validate product exists and is available
        product = self.product_repo.get_by_id(request.product_id)
        if not product:
            return CartOperationResponse(
                success=False,
                message="Product not found",
                cart=None,
            )

        # Check if product is active
        if product.status.value != "active":
            return CartOperationResponse(
                success=False,
                message="This product is currently unavailable",
                cart=None,
            )

        # Check stock availability
        if product.quantity <= 0:
            return CartOperationResponse(
                success=False,
                message="This product is out of stock",
                cart=None,
            )

        if request.quantity > product.quantity:
            return CartOperationResponse(
                success=False,
                message=f"Only {product.quantity} units available in stock",
                cart=None,
            )

        # Get or create cart
        cart = self.cart_repo.get_or_create_cart(user_id)

        # Check if product already in cart
        existing_item = self.cart_repo.get_cart_item_by_product(
            cart.id, request.product_id
        )

        if existing_item:
            # Update quantity instead of adding new item
            new_quantity = existing_item.quantity + request.quantity

            # Validate against stock
            if new_quantity > product.quantity:
                return CartOperationResponse(
                    success=False,
                    message=f"Cannot add more. Only {product.quantity} units available "
                    f"({existing_item.quantity} already in cart)",
                    cart=None,
                )

            updated_item = self.cart_repo.update_item_quantity(
                existing_item.id, new_quantity
            )
            if not updated_item:
                return CartOperationResponse(
                    success=False,
                    message="Failed to update cart item",
                    cart=None,
                )
            cart_item = updated_item
            message = f"Updated quantity to {new_quantity} in your cart"
        else:
            # Add new item
            cart_item = self.cart_repo.add_item(
                cart_id=cart.id,
                product_id=request.product_id,
                quantity=request.quantity,
                unit_price=product.price,
            )
            message = f"Added {product.name} to your cart"

        # Build response
        item_response = self._build_cart_item_response(cart_item, product)

        # Get updated cart summary
        all_items = self.cart_repo.get_cart_items(cart.id)
        response_items: list[CartItemResponse] = []
        for ci in all_items:
            p = self.product_repo.get_by_id(ci.product_id)
            if p:
                response_items.append(self._build_cart_item_response(ci, p))

        summary = self._calculate_summary(response_items)

        return CartItemAddedResponse(
            success=True,
            message=message,
            item=item_response,
            cart_summary=summary,
        )

    def update_cart_item(
        self,
        user_id: UUID,
        item_id: UUID,
        request: UpdateCartItemRequest,
    ) -> CartOperationResponse:
        """Update a cart item's quantity.

        Args:
            user_id: User's UUID.
            item_id: Cart item's UUID.
            request: Update request with new quantity.

        Returns:
            CartOperationResponse with updated cart.
        """
        # Get user's cart
        cart = self.cart_repo.get_cart_by_user_id(user_id)
        if not cart:
            return CartOperationResponse(
                success=False,
                message="Cart not found",
                cart=None,
            )

        # Get cart item
        cart_item = self.cart_repo.get_cart_item(item_id)
        if not cart_item:
            return CartOperationResponse(
                success=False,
                message="Item not found in cart",
                cart=None,
            )

        # Verify item belongs to user's cart
        if cart_item.cart_id != cart.id:
            return CartOperationResponse(
                success=False,
                message="Item not found in your cart",
                cart=None,
            )

        # Get product to check stock
        product = self.product_repo.get_by_id(cart_item.product_id)
        if not product:
            return CartOperationResponse(
                success=False,
                message="Product no longer available",
                cart=None,
            )

        # Validate quantity against stock
        if request.quantity > product.quantity:
            return CartOperationResponse(
                success=False,
                message=f"Only {product.quantity} units available in stock",
                cart=None,
            )

        # Update quantity
        updated_item = self.cart_repo.update_item_quantity(
            item_id, request.quantity
        )
        if not updated_item:
            return CartOperationResponse(
                success=False,
                message="Failed to update cart item",
                cart=None,
            )

        # Get updated cart
        cart_response = self.get_cart(user_id)
        if isinstance(cart_response, EmptyCartResponse):
            return CartOperationResponse(
                success=True,
                message="Quantity updated",
                cart=None,
            )

        return CartOperationResponse(
            success=True,
            message=f"Quantity updated to {request.quantity}",
            cart=cart_response,
        )

    def remove_from_cart(
        self, user_id: UUID, item_id: UUID
    ) -> CartOperationResponse:
        """Remove an item from the cart.

        Args:
            user_id: User's UUID.
            item_id: Cart item's UUID.

        Returns:
            CartOperationResponse with updated cart.
        """
        # Get user's cart
        cart = self.cart_repo.get_cart_by_user_id(user_id)
        if not cart:
            return CartOperationResponse(
                success=False,
                message="Cart not found",
                cart=None,
            )

        # Get cart item
        cart_item = self.cart_repo.get_cart_item(item_id)
        if not cart_item:
            return CartOperationResponse(
                success=False,
                message="Item not found in cart",
                cart=None,
            )

        # Verify item belongs to user's cart
        if cart_item.cart_id != cart.id:
            return CartOperationResponse(
                success=False,
                message="Item not found in your cart",
                cart=None,
            )

        # Get product name for message
        product = self.product_repo.get_by_id(cart_item.product_id)
        product_name = product.name if product else "Item"

        # Remove item
        removed = self.cart_repo.remove_item(item_id)
        if not removed:
            return CartOperationResponse(
                success=False,
                message="Failed to remove item from cart",
                cart=None,
            )

        # Get updated cart
        cart_response = self.get_cart(user_id)
        if isinstance(cart_response, EmptyCartResponse):
            return CartOperationResponse(
                success=True,
                message=f"{product_name} removed from cart",
                cart=None,
            )

        return CartOperationResponse(
            success=True,
            message=f"{product_name} removed from cart",
            cart=cart_response,
        )

    def clear_cart(self, user_id: UUID) -> CartOperationResponse:
        """Clear all items from the cart.

        Args:
            user_id: User's UUID.

        Returns:
            CartOperationResponse confirming cart cleared.
        """
        # Get user's cart
        cart = self.cart_repo.get_cart_by_user_id(user_id)
        if not cart:
            return CartOperationResponse(
                success=True,
                message="Cart is already empty",
                cart=None,
            )

        # Clear items
        removed_count = self.cart_repo.clear_cart(cart.id)

        return CartOperationResponse(
            success=True,
            message=f"Removed {removed_count} item(s) from cart"
            if removed_count > 0
            else "Cart is already empty",
            cart=None,
        )

    def get_cart_count(self, user_id: UUID) -> int:
        """Get the total number of items in user's cart.

        Args:
            user_id: User's UUID.

        Returns:
            Total quantity of all items in cart.
        """
        cart = self.cart_repo.get_cart_by_user_id(user_id)
        if not cart:
            return 0
        return self.cart_repo.get_cart_item_count(cart.id)

    def validate_cart_stock(self, user_id: UUID) -> list[dict]:
        """Validate all cart items against current stock.

        Useful before checkout to ensure all items are available.

        Args:
            user_id: User's UUID.

        Returns:
            List of issues (empty if all valid).
        """
        cart = self.cart_repo.get_cart_by_user_id(user_id)
        if not cart:
            return []

        cart_items = self.cart_repo.get_cart_items(cart.id)
        issues: list[dict] = []

        for item in cart_items:
            product = self.product_repo.get_by_id(item.product_id)
            if not product:
                issues.append({
                    "item_id": str(item.id),
                    "product_id": str(item.product_id),
                    "issue": "Product no longer available",
                    "action": "remove",
                })
            elif product.status.value != "active":
                issues.append({
                    "item_id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": product.name,
                    "issue": "Product is currently unavailable",
                    "action": "remove",
                })
            elif product.quantity <= 0:
                issues.append({
                    "item_id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": product.name,
                    "issue": "Product is out of stock",
                    "action": "remove",
                })
            elif item.quantity > product.quantity:
                issues.append({
                    "item_id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": product.name,
                    "issue": f"Only {product.quantity} available (you have {item.quantity})",
                    "action": "reduce",
                    "max_quantity": product.quantity,
                })

        return issues
