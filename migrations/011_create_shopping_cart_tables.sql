-- Migration: 011_create_shopping_cart_tables
-- Description: Create shopping cart and cart_items tables for US-013
-- User Story: US-013 (Shopping Cart Management)
-- Created: 2025-12-10

-- ============================================================================
-- SHOPPING CARTS TABLE
-- Stores cart per user with summary information
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.shopping_carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one cart per user
    CONSTRAINT unique_user_cart UNIQUE (user_id)
);

-- ============================================================================
-- CART ITEMS TABLE
-- Stores individual items in each cart
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL REFERENCES public.shopping_carts(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique product per cart (quantity is updated instead of duplicate entries)
    CONSTRAINT unique_cart_product UNIQUE (cart_id, product_id),

    -- Quantity must be positive
    CONSTRAINT positive_quantity CHECK (quantity > 0),

    -- Price must be non-negative
    CONSTRAINT non_negative_price CHECK (unit_price >= 0)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for user cart lookup
CREATE INDEX IF NOT EXISTS idx_shopping_carts_user_id ON public.shopping_carts(user_id);

-- Index for cart items lookup
CREATE INDEX IF NOT EXISTS idx_cart_items_cart_id ON public.cart_items(cart_id);

-- Index for product in cart lookup
CREATE INDEX IF NOT EXISTS idx_cart_items_product_id ON public.cart_items(product_id);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for shopping_carts
DROP TRIGGER IF EXISTS update_shopping_carts_updated_at ON public.shopping_carts;
CREATE TRIGGER update_shopping_carts_updated_at
    BEFORE UPDATE ON public.shopping_carts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for cart_items
DROP TRIGGER IF EXISTS update_cart_items_updated_at ON public.cart_items;
CREATE TRIGGER update_cart_items_updated_at
    BEFORE UPDATE ON public.cart_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on shopping_carts
ALTER TABLE public.shopping_carts ENABLE ROW LEVEL SECURITY;

-- Enable RLS on cart_items
ALTER TABLE public.cart_items ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own cart
CREATE POLICY shopping_carts_user_policy ON public.shopping_carts
    FOR ALL
    USING (auth.uid() = user_id);

-- Policy: Users can only access items in their own cart
CREATE POLICY cart_items_user_policy ON public.cart_items
    FOR ALL
    USING (
        cart_id IN (
            SELECT id FROM public.shopping_carts WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE public.shopping_carts IS 'Shopping carts for users (one per user)';
COMMENT ON TABLE public.cart_items IS 'Individual items in shopping carts';

COMMENT ON COLUMN public.shopping_carts.user_id IS 'Reference to the user who owns this cart';
COMMENT ON COLUMN public.cart_items.cart_id IS 'Reference to the shopping cart';
COMMENT ON COLUMN public.cart_items.product_id IS 'Reference to the product';
COMMENT ON COLUMN public.cart_items.quantity IS 'Quantity of the product in cart';
COMMENT ON COLUMN public.cart_items.unit_price IS 'Price per unit at time of adding to cart';
