-- Migration: 005_pricing_management
-- Description: Add pricing features including discounts, bulk pricing, and price history
-- User Story: US-010 (Product Pricing Management)
-- Created: 2025-12-10

-- ============================================================================
-- 1. ADD DISCOUNT FIELDS TO PRODUCTS TABLE
-- ============================================================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_type VARCHAR(20) DEFAULT NULL
    CHECK (discount_type IS NULL OR discount_type IN ('percentage', 'fixed'));

ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_value DECIMAL(10, 2) DEFAULT NULL;

ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_start_date TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_end_date TIMESTAMPTZ DEFAULT NULL;

COMMENT ON COLUMN products.discount_type IS 'Type of discount: percentage or fixed amount';
COMMENT ON COLUMN products.discount_value IS 'Discount value (percentage 0-100 or fixed amount)';
COMMENT ON COLUMN products.discount_start_date IS 'When discount becomes active';
COMMENT ON COLUMN products.discount_end_date IS 'When discount expires (NULL = no expiry)';

-- ============================================================================
-- 2. CREATE BULK PRICING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS bulk_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    min_quantity INTEGER NOT NULL CHECK (min_quantity > 0),
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(product_id, min_quantity)
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_bulk_pricing_product_id ON bulk_pricing(product_id);

-- Enable RLS
ALTER TABLE bulk_pricing ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY bulk_pricing_select ON bulk_pricing FOR SELECT USING (true);
CREATE POLICY bulk_pricing_insert ON bulk_pricing FOR INSERT WITH CHECK (true);
CREATE POLICY bulk_pricing_update ON bulk_pricing FOR UPDATE USING (true);
CREATE POLICY bulk_pricing_delete ON bulk_pricing FOR DELETE USING (true);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_bulk_pricing_updated_at ON bulk_pricing;
CREATE TRIGGER update_bulk_pricing_updated_at
    BEFORE UPDATE ON bulk_pricing
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE bulk_pricing IS 'Tiered bulk pricing rules for products';
COMMENT ON COLUMN bulk_pricing.min_quantity IS 'Minimum quantity to qualify for this price tier';
COMMENT ON COLUMN bulk_pricing.price IS 'Price per unit at this quantity tier';

-- ============================================================================
-- 3. CREATE PRICE HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    previous_price DECIMAL(10, 2) NOT NULL,
    new_price DECIMAL(10, 2) NOT NULL,
    change_type VARCHAR(20) NOT NULL DEFAULT 'manual'
        CHECK (change_type IN ('manual', 'discount_applied', 'discount_removed', 'bulk_update')),
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_created_at ON price_history(created_at DESC);

-- Enable RLS
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY price_history_select ON price_history FOR SELECT USING (true);
CREATE POLICY price_history_insert ON price_history FOR INSERT WITH CHECK (true);

COMMENT ON TABLE price_history IS 'Historical record of product price changes';

-- ============================================================================
-- 4. CREATE FUNCTION TO LOG PRICE CHANGES
-- ============================================================================
CREATE OR REPLACE FUNCTION log_price_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log when price actually changes
    IF TG_OP = 'UPDATE' AND OLD.price IS DISTINCT FROM NEW.price THEN
        INSERT INTO price_history (product_id, previous_price, new_price, change_type)
        VALUES (NEW.id, OLD.price, NEW.price, 'manual');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic price history logging
DROP TRIGGER IF EXISTS log_price_change_trigger ON products;
CREATE TRIGGER log_price_change_trigger
    AFTER UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION log_price_change();

-- ============================================================================
-- 5. CREATE VIEW FOR PRODUCTS WITH EFFECTIVE PRICES
-- ============================================================================
CREATE OR REPLACE VIEW products_with_pricing AS
SELECT
    p.*,
    -- Calculate effective price considering active discount
    CASE
        WHEN p.discount_type IS NOT NULL
             AND (p.discount_start_date IS NULL OR p.discount_start_date <= NOW())
             AND (p.discount_end_date IS NULL OR p.discount_end_date > NOW())
        THEN
            CASE p.discount_type
                WHEN 'percentage' THEN ROUND(p.price * (1 - p.discount_value / 100), 2)
                WHEN 'fixed' THEN GREATEST(p.price - p.discount_value, 0.01)
            END
        ELSE p.price
    END AS effective_price,
    -- Flag for active discount
    CASE
        WHEN p.discount_type IS NOT NULL
             AND (p.discount_start_date IS NULL OR p.discount_start_date <= NOW())
             AND (p.discount_end_date IS NULL OR p.discount_end_date > NOW())
        THEN true
        ELSE false
    END AS has_active_discount,
    -- Get lowest bulk price
    (
        SELECT MIN(bp.price)
        FROM bulk_pricing bp
        WHERE bp.product_id = p.id
    ) AS lowest_bulk_price,
    -- Check if has bulk pricing
    EXISTS(SELECT 1 FROM bulk_pricing bp WHERE bp.product_id = p.id) AS has_bulk_pricing
FROM products p;

COMMENT ON VIEW products_with_pricing IS 'Products with calculated effective prices and discount info';

-- ============================================================================
-- 6. FUNCTION TO GET BULK PRICE FOR QUANTITY
-- ============================================================================
CREATE OR REPLACE FUNCTION get_bulk_price(p_product_id UUID, p_quantity INTEGER)
RETURNS DECIMAL(10, 2) AS $$
DECLARE
    bulk_price DECIMAL(10, 2);
    base_price DECIMAL(10, 2);
BEGIN
    -- Get the applicable bulk price tier
    SELECT bp.price INTO bulk_price
    FROM bulk_pricing bp
    WHERE bp.product_id = p_product_id
      AND bp.min_quantity <= p_quantity
    ORDER BY bp.min_quantity DESC
    LIMIT 1;

    -- If no bulk price applies, get the regular price
    IF bulk_price IS NULL THEN
        SELECT price INTO base_price FROM products WHERE id = p_product_id;
        RETURN base_price;
    END IF;

    RETURN bulk_price;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_bulk_price IS 'Get applicable price for a product based on quantity (considering bulk pricing)';

-- ============================================================================
-- 7. CREATE PRICE DROP NOTIFICATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    previous_price DECIMAL(10, 2) NOT NULL,
    new_price DECIMAL(10, 2) NOT NULL,
    notification_type VARCHAR(20) NOT NULL DEFAULT 'price_drop'
        CHECK (notification_type IN ('price_drop', 'discount_applied', 'back_in_stock')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_price_notifications_user_id ON price_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_price_notifications_product_id ON price_notifications(product_id);
CREATE INDEX IF NOT EXISTS idx_price_notifications_is_read ON price_notifications(is_read);

-- Enable RLS
ALTER TABLE price_notifications ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY price_notifications_select ON price_notifications FOR SELECT USING (true);
CREATE POLICY price_notifications_insert ON price_notifications FOR INSERT WITH CHECK (true);
CREATE POLICY price_notifications_update ON price_notifications FOR UPDATE USING (true);

COMMENT ON TABLE price_notifications IS 'Notifications for users about price changes on products they follow';

-- ============================================================================
-- 8. CREATE WISHLIST TABLE (for price notifications)
-- ============================================================================
CREATE TABLE IF NOT EXISTS wishlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_wishlists_user_id ON wishlists(user_id);
CREATE INDEX IF NOT EXISTS idx_wishlists_product_id ON wishlists(product_id);

-- Enable RLS
ALTER TABLE wishlists ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY wishlists_select ON wishlists FOR SELECT USING (true);
CREATE POLICY wishlists_insert ON wishlists FOR INSERT WITH CHECK (true);
CREATE POLICY wishlists_delete ON wishlists FOR DELETE USING (true);

COMMENT ON TABLE wishlists IS 'User wishlists for tracking products';

-- ============================================================================
-- 9. FUNCTION TO NOTIFY USERS OF PRICE DROPS
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_price_drop()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify when price decreases
    IF TG_OP = 'UPDATE' AND OLD.price > NEW.price THEN
        -- Insert notifications for users who have this product in wishlist
        INSERT INTO price_notifications (product_id, user_id, previous_price, new_price, notification_type)
        SELECT NEW.id, w.user_id, OLD.price, NEW.price, 'price_drop'
        FROM wishlists w
        WHERE w.product_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for price drop notifications
DROP TRIGGER IF EXISTS notify_price_drop_trigger ON products;
CREATE TRIGGER notify_price_drop_trigger
    AFTER UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION notify_price_drop();
