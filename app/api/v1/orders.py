"""Orders API endpoints for order management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from supabase import Client

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.user import UserInDB

router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderItemResponse(BaseModel):
    """Order item response model."""

    id: UUID
    product_id: UUID
    product_name: str | None = None
    product_image: str | None = None
    quantity: int
    unit_price: float


class OrderResponse(BaseModel):
    """Order response model."""

    id: UUID
    user_id: UUID
    status: str
    total_amount: float
    created_at: str
    updated_at: str
    items: list[OrderItemResponse] = []


class OrderListResponse(BaseModel):
    """Order list response model."""

    orders: list[OrderResponse]
    total: int


@router.get(
    "",
    response_model=OrderListResponse,
    summary="Get user orders",
    description="Get all orders for the current user, optionally filtered by status.",
)
async def get_orders(
    status_filter: str | None = Query(None, alias="status"),
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> OrderListResponse:
    """Get all orders for the current user."""
    query = db_client.table("orders").select("*").eq("user_id", str(current_user.id))

    if status_filter:
        query = query.eq("status", status_filter)

    query = query.order("created_at", desc=True)
    result = query.execute()

    orders = []
    for order in result.data or []:
        # Get order items
        items_result = (
            db_client.table("order_items")
            .select("*")
            .eq("order_id", order["id"])
            .execute()
        )

        items = []
        for item in items_result.data or []:
            # Get product info
            product_result = (
                db_client.table("products")
                .select("name, images")
                .eq("id", item["product_id"])
                .single()
                .execute()
            )
            product = product_result.data if product_result.data else {}

            items.append(
                OrderItemResponse(
                    id=item["id"],
                    product_id=item["product_id"],
                    product_name=product.get("name"),
                    product_image=product.get("images", [None])[0]
                    if product.get("images")
                    else None,
                    quantity=item["quantity"],
                    unit_price=float(item["unit_price"]),
                )
            )

        orders.append(
            OrderResponse(
                id=order["id"],
                user_id=order["user_id"],
                status=order["status"],
                total_amount=float(order["total_amount"]),
                created_at=order["created_at"],
                updated_at=order["updated_at"],
                items=items,
            )
        )

    return OrderListResponse(orders=orders, total=len(orders))


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
    description="Get details of a specific order.",
)
async def get_order(
    order_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> OrderResponse:
    """Get details of a specific order."""
    result = (
        db_client.table("orders")
        .select("*")
        .eq("id", str(order_id))
        .eq("user_id", str(current_user.id))
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order = result.data

    # Get order items
    items_result = (
        db_client.table("order_items")
        .select("*")
        .eq("order_id", str(order_id))
        .execute()
    )

    items = []
    for item in items_result.data or []:
        product_result = (
            db_client.table("products")
            .select("name, images")
            .eq("id", item["product_id"])
            .single()
            .execute()
        )
        product = product_result.data if product_result.data else {}

        items.append(
            OrderItemResponse(
                id=item["id"],
                product_id=item["product_id"],
                product_name=product.get("name"),
                product_image=product.get("images", [None])[0]
                if product.get("images")
                else None,
                quantity=item["quantity"],
                unit_price=float(item["unit_price"]),
            )
        )

    return OrderResponse(
        id=order["id"],
        user_id=order["user_id"],
        status=order["status"],
        total_amount=float(order["total_amount"]),
        created_at=order["created_at"],
        updated_at=order["updated_at"],
        items=items,
    )


@router.post(
    "/{order_id}/cancel",
    summary="Cancel order",
    description="Cancel a pending order.",
)
async def cancel_order(
    order_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    db_client: Client = Depends(get_supabase_client),
) -> dict:
    """Cancel a pending order."""
    # Check if order exists and belongs to user
    result = (
        db_client.table("orders")
        .select("*")
        .eq("id", str(order_id))
        .eq("user_id", str(current_user.id))
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if result.data["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled",
        )

    # Update order status
    db_client.table("orders").update({"status": "cancelled"}).eq(
        "id", str(order_id)
    ).execute()

    return {"message": "Order cancelled successfully"}
