"""Admin API endpoints for dashboard and management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.dependencies import get_current_active_user
from app.db.supabase import get_supabase_client
from app.models.user import UserInDB

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminStats(BaseModel):
    """Dashboard statistics."""

    total_users: int
    total_farmers: int
    total_products: int
    total_orders: int
    active_products: int
    pending_farmers: int


class UserListItem(BaseModel):
    """User item for admin list."""

    id: str
    email: str
    full_name: str
    role: str
    email_verified: bool
    created_at: str


class UserListResponse(BaseModel):
    """Response for user list."""

    users: list[UserListItem]
    total: int
    page: int
    page_size: int


class FarmerListItem(BaseModel):
    """Farmer item for admin list."""

    id: str
    user_id: str
    email: str
    full_name: str
    farm_name: str | None
    profile_completed: bool
    created_at: str


class FarmerListResponse(BaseModel):
    """Response for farmer list."""

    farmers: list[FarmerListItem]
    total: int
    page: int
    page_size: int


class ProductListItem(BaseModel):
    """Product item for admin list."""

    id: str
    name: str
    category: str
    price: float
    quantity: int
    status: str
    farmer_name: str | None
    created_at: str


class ProductListResponse(BaseModel):
    """Response for product list."""

    products: list[ProductListItem]
    total: int
    page: int
    page_size: int


class UserUpdateRequest(BaseModel):
    """Request to update a user."""

    full_name: str | None = None
    role: str | None = None
    email_verified: bool | None = None


class ProductUpdateRequest(BaseModel):
    """Request to update a product."""

    name: str | None = None
    category: str | None = None
    price: float | None = None
    quantity: int | None = None
    status: str | None = None


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


def require_admin(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """Dependency to require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    current_user: UserInDB = Depends(require_admin),
) -> AdminStats:
    """Get dashboard statistics."""
    db = get_supabase_client()

    # Count users
    users_result = db.table("users").select("id", count="exact").execute()
    total_users = users_result.count or 0

    # Count farmers (users with role='farmer')
    farmers_result = db.table("users").select("id", count="exact").eq("role", "farmer").execute()
    total_farmers = farmers_result.count or 0

    # Count products
    products_result = db.table("products").select("id", count="exact").execute()
    total_products = products_result.count or 0

    # Count active products
    active_products_result = (
        db.table("products").select("id", count="exact").eq("status", "active").execute()
    )
    active_products = active_products_result.count or 0

    # Count orders (if table exists)
    try:
        orders_result = db.table("orders").select("id", count="exact").execute()
        total_orders = orders_result.count or 0
    except Exception:
        total_orders = 0

    # Count pending farmers (farmers table where profile_completed = false)
    try:
        pending_result = (
            db.table("farmers")
            .select("id", count="exact")
            .eq("profile_completed", False)
            .execute()
        )
        pending_farmers = pending_result.count or 0
    except Exception:
        pending_farmers = 0

    return AdminStats(
        total_users=total_users,
        total_farmers=total_farmers,
        total_products=total_products,
        total_orders=total_orders,
        active_products=active_products,
        pending_farmers=pending_farmers,
    )


@router.get("/users", response_model=UserListResponse)
def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    current_user: UserInDB = Depends(require_admin),
) -> UserListResponse:
    """Get list of all users."""
    db = get_supabase_client()

    # Build query
    query = db.table("users").select(
        "id, email, full_name, role, email_verified, created_at",
        count="exact",
    )

    if role:
        query = query.eq("role", role)

    # Paginate
    offset = (page - 1) * page_size
    result = (
        query.order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    users = [
        UserListItem(
            id=str(u["id"]),
            email=u["email"],
            full_name=u["full_name"] or "",
            role=u["role"] or "consumer",
            email_verified=u["email_verified"] or False,
            created_at=str(u["created_at"]),
        )
        for u in (result.data or [])
    ]

    return UserListResponse(
        users=users,
        total=result.count or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/farmers", response_model=FarmerListResponse)
def get_farmers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: UserInDB = Depends(require_admin),
) -> FarmerListResponse:
    """Get list of all farmers with their profiles."""
    db = get_supabase_client()

    # Get farmer users
    offset = (page - 1) * page_size
    users_result = (
        db.table("users")
        .select("id, email, full_name, created_at", count="exact")
        .eq("role", "farmer")
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    farmers = []
    for user in users_result.data or []:
        # Try to get farmer profile
        farm_name = None
        profile_completed = False

        try:
            farmer_profile = (
                db.table("farmers")
                .select("id, farm_name, profile_completed")
                .eq("user_id", user["id"])
                .single()
                .execute()
            )
            if farmer_profile.data:
                farm_name = farmer_profile.data.get("farm_name")
                profile_completed = farmer_profile.data.get("profile_completed", False)
        except Exception:
            pass

        farmers.append(
            FarmerListItem(
                id=str(user["id"]),
                user_id=str(user["id"]),
                email=user["email"],
                full_name=user["full_name"] or "",
                farm_name=farm_name,
                profile_completed=profile_completed,
                created_at=str(user["created_at"]),
            )
        )

    return FarmerListResponse(
        farmers=farmers,
        total=users_result.count or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/products", response_model=ProductListResponse)
def get_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    current_user: UserInDB = Depends(require_admin),
) -> ProductListResponse:
    """Get list of all products."""
    db = get_supabase_client()

    # Build query
    query = db.table("products").select(
        "id, name, category, price, quantity, status, farmer_id, created_at",
        count="exact",
    )

    if status:
        query = query.eq("status", status)

    # Paginate
    offset = (page - 1) * page_size
    result = (
        query.order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    products = []
    for p in result.data or []:
        # Get farmer name
        farmer_name = None
        try:
            farmer = (
                db.table("users")
                .select("full_name")
                .eq("id", p["farmer_id"])
                .single()
                .execute()
            )
            if farmer.data:
                farmer_name = farmer.data.get("full_name")
        except Exception:
            pass

        products.append(
            ProductListItem(
                id=str(p["id"]),
                name=p["name"],
                category=p["category"],
                price=float(p["price"]),
                quantity=p["quantity"],
                status=p["status"],
                farmer_name=farmer_name,
                created_at=str(p["created_at"]),
            )
        )

    return ProductListResponse(
        products=products,
        total=result.count or 0,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# User CRUD Operations
# ============================================================================


@router.get("/users/{user_id}", response_model=UserListItem)
def get_user(
    user_id: str,
    current_user: UserInDB = Depends(require_admin),
) -> UserListItem:
    """Get a single user by ID."""
    db = get_supabase_client()

    result = (
        db.table("users")
        .select("id, email, full_name, role, email_verified, created_at")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    u = result.data
    return UserListItem(
        id=str(u["id"]),
        email=u["email"],
        full_name=u["full_name"] or "",
        role=u["role"] or "consumer",
        email_verified=u["email_verified"] or False,
        created_at=str(u["created_at"]),
    )


@router.put("/users/{user_id}", response_model=UserListItem)
def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: UserInDB = Depends(require_admin),
) -> UserListItem:
    """Update a user's details."""
    db = get_supabase_client()

    # Prevent admin from demoting themselves
    if str(current_user.id) == user_id and request.role and request.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own admin role",
        )

    # Build update data
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.role is not None:
        if request.role not in ["consumer", "farmer", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be consumer, farmer, or admin",
            )
        update_data["role"] = request.role
    if request.email_verified is not None:
        update_data["email_verified"] = request.email_verified

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = (
        db.table("users")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Fetch updated user
    updated = (
        db.table("users")
        .select("id, email, full_name, role, email_verified, created_at")
        .eq("id", user_id)
        .single()
        .execute()
    )

    u = updated.data
    return UserListItem(
        id=str(u["id"]),
        email=u["email"],
        full_name=u["full_name"] or "",
        role=u["role"] or "consumer",
        email_verified=u["email_verified"] or False,
        created_at=str(u["created_at"]),
    )


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: str,
    current_user: UserInDB = Depends(require_admin),
) -> MessageResponse:
    """Delete a user."""
    db = get_supabase_client()

    # Prevent admin from deleting themselves
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Check if user exists
    check = db.table("users").select("id, role").eq("id", user_id).single().execute()
    if not check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Delete associated data first (products if farmer)
    if check.data.get("role") == "farmer":
        db.table("products").delete().eq("farmer_id", user_id).execute()
        # Try to delete farmer profile
        try:
            db.table("farmers").delete().eq("user_id", user_id).execute()
        except Exception:
            pass

    # Delete user
    db.table("users").delete().eq("id", user_id).execute()

    return MessageResponse(message="User deleted successfully")


# ============================================================================
# Product CRUD Operations
# ============================================================================


@router.get("/products/{product_id}", response_model=ProductListItem)
def get_product(
    product_id: str,
    current_user: UserInDB = Depends(require_admin),
) -> ProductListItem:
    """Get a single product by ID."""
    db = get_supabase_client()

    result = (
        db.table("products")
        .select("id, name, category, price, quantity, status, farmer_id, created_at")
        .eq("id", product_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    p = result.data
    farmer_name = None
    try:
        farmer = (
            db.table("users")
            .select("full_name")
            .eq("id", p["farmer_id"])
            .single()
            .execute()
        )
        if farmer.data:
            farmer_name = farmer.data.get("full_name")
    except Exception:
        pass

    return ProductListItem(
        id=str(p["id"]),
        name=p["name"],
        category=p["category"],
        price=float(p["price"]),
        quantity=p["quantity"],
        status=p["status"],
        farmer_name=farmer_name,
        created_at=str(p["created_at"]),
    )


@router.put("/products/{product_id}", response_model=ProductListItem)
def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    current_user: UserInDB = Depends(require_admin),
) -> ProductListItem:
    """Update a product's details."""
    db = get_supabase_client()

    # Build update data
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.category is not None:
        update_data["category"] = request.category
    if request.price is not None:
        if request.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price cannot be negative",
            )
        update_data["price"] = request.price
    if request.quantity is not None:
        if request.quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative",
            )
        update_data["quantity"] = request.quantity
    if request.status is not None:
        if request.status not in ["active", "inactive", "archived"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be active, inactive, or archived",
            )
        update_data["status"] = request.status

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = (
        db.table("products")
        .update(update_data)
        .eq("id", product_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Fetch updated product
    updated = (
        db.table("products")
        .select("id, name, category, price, quantity, status, farmer_id, created_at")
        .eq("id", product_id)
        .single()
        .execute()
    )

    p = updated.data
    farmer_name = None
    try:
        farmer = (
            db.table("users")
            .select("full_name")
            .eq("id", p["farmer_id"])
            .single()
            .execute()
        )
        if farmer.data:
            farmer_name = farmer.data.get("full_name")
    except Exception:
        pass

    return ProductListItem(
        id=str(p["id"]),
        name=p["name"],
        category=p["category"],
        price=float(p["price"]),
        quantity=p["quantity"],
        status=p["status"],
        farmer_name=farmer_name,
        created_at=str(p["created_at"]),
    )


@router.delete("/products/{product_id}", response_model=MessageResponse)
def delete_product(
    product_id: str,
    current_user: UserInDB = Depends(require_admin),
) -> MessageResponse:
    """Delete a product."""
    db = get_supabase_client()

    # Check if product exists
    check = db.table("products").select("id").eq("id", product_id).single().execute()
    if not check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Delete product
    db.table("products").delete().eq("id", product_id).execute()

    return MessageResponse(message="Product deleted successfully")
