-- Migration: 004_product_availability_management
-- Description: Add low-stock threshold and inventory management features for US-008 and US-009
-- User Stories: US-008 (Remove/Archive Product), US-009 (Availability Management)
-- Created: 2025-12-10

-- ============================================================================
-- 1. ADD LOW-STOCK THRESHOLD COLUMN TO PRODUCTS
-- ============================================================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INTEGER NOT NULL DEFAULT 10;

COMMENT ON COLUMN products.low_stock_threshold IS 'Threshold for low-stock alerts (default: 10 units)';

-- ============================================================================
-- 2. CREATE LOW-STOCK ALERTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS low_stock_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    farmer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    previous_quantity INTEGER NOT NULL,
    current_quantity INTEGER NOT NULL,
    threshold INTEGER NOT NULL,
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('low_stock', 'out_of_stock', 'back_in_stock')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_farmer_id ON low_stock_alerts(farmer_id);
CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_product_id ON low_stock_alerts(product_id);
CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_is_read ON low_stock_alerts(is_read);
CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_created_at ON low_stock_alerts(created_at DESC);

-- Enable RLS
ALTER TABLE low_stock_alerts ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY low_stock_alerts_select ON low_stock_alerts
    FOR SELECT USING (true);

CREATE POLICY low_stock_alerts_insert ON low_stock_alerts
    FOR INSERT WITH CHECK (true);

CREATE POLICY low_stock_alerts_update ON low_stock_alerts
    FOR UPDATE USING (true);

COMMENT ON TABLE low_stock_alerts IS 'Alerts for farmers when product stock falls below threshold';

-- ============================================================================
-- 3. CREATE FUNCTION TO CHECK AND CREATE LOW-STOCK ALERTS
-- ============================================================================
CREATE OR REPLACE FUNCTION check_low_stock_alert()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check on UPDATE when quantity changes
    IF TG_OP = 'UPDATE' AND OLD.quantity IS DISTINCT FROM NEW.quantity THEN

        -- Check for out-of-stock (quantity became 0)
        IF OLD.quantity > 0 AND NEW.quantity = 0 THEN
            INSERT INTO low_stock_alerts (product_id, farmer_id, previous_quantity, current_quantity, threshold, alert_type)
            VALUES (NEW.id, NEW.farmer_id, OLD.quantity, NEW.quantity, NEW.low_stock_threshold, 'out_of_stock');

        -- Check for back-in-stock (quantity was 0, now > 0)
        ELSIF OLD.quantity = 0 AND NEW.quantity > 0 THEN
            INSERT INTO low_stock_alerts (product_id, farmer_id, previous_quantity, current_quantity, threshold, alert_type)
            VALUES (NEW.id, NEW.farmer_id, OLD.quantity, NEW.quantity, NEW.low_stock_threshold, 'back_in_stock');

        -- Check for low-stock (crossed threshold downward)
        ELSIF OLD.quantity > NEW.low_stock_threshold AND NEW.quantity <= NEW.low_stock_threshold AND NEW.quantity > 0 THEN
            INSERT INTO low_stock_alerts (product_id, farmer_id, previous_quantity, current_quantity, threshold, alert_type)
            VALUES (NEW.id, NEW.farmer_id, OLD.quantity, NEW.quantity, NEW.low_stock_threshold, 'low_stock');
        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for low-stock alerts
DROP TRIGGER IF EXISTS check_low_stock_alert_trigger ON products;
CREATE TRIGGER check_low_stock_alert_trigger
    AFTER UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION check_low_stock_alert();

-- ============================================================================
-- 4. CREATE PENDING ORDERS VIEW (placeholder for order integration)
-- ============================================================================
-- Note: This assumes an orders table will exist. For now, create a simple structure
-- to support the "cannot delete product with pending orders" requirement

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')),
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY orders_select ON orders FOR SELECT USING (true);
CREATE POLICY orders_insert ON orders FOR INSERT WITH CHECK (true);
CREATE POLICY orders_update ON orders FOR UPDATE USING (true);

CREATE POLICY order_items_select ON order_items FOR SELECT USING (true);
CREATE POLICY order_items_insert ON order_items FOR INSERT WITH CHECK (true);

-- Trigger for orders updated_at
DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE orders IS 'Customer orders';
COMMENT ON TABLE order_items IS 'Line items in customer orders';

-- ============================================================================
-- 5. FUNCTION TO CHECK IF PRODUCT HAS PENDING ORDERS
-- ============================================================================
CREATE OR REPLACE FUNCTION product_has_pending_orders(p_product_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    pending_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO pending_count
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE oi.product_id = p_product_id
    AND o.status IN ('pending', 'confirmed', 'processing');

    RETURN pending_count > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION product_has_pending_orders IS 'Check if a product has any unfulfilled orders';

-- ============================================================================
-- 6. FUNCTION TO DECREMENT INVENTORY ON ORDER
-- ============================================================================
CREATE OR REPLACE FUNCTION decrement_inventory_on_order()
RETURNS TRIGGER AS $$
BEGIN
    -- Only decrement on INSERT (new order item)
    IF TG_OP = 'INSERT' THEN
        UPDATE products
        SET quantity = quantity - NEW.quantity
        WHERE id = NEW.product_id
        AND quantity >= NEW.quantity;

        -- Check if update was successful
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Insufficient inventory for product %', NEW.product_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for inventory decrement
DROP TRIGGER IF EXISTS decrement_inventory_trigger ON order_items;
CREATE TRIGGER decrement_inventory_trigger
    AFTER INSERT ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION decrement_inventory_on_order();

-- ============================================================================
-- 7. VIEW FOR PRODUCTS WITH STOCK STATUS
-- ============================================================================
CREATE OR REPLACE VIEW product_stock_status AS
SELECT
    p.id,
    p.farmer_id,
    p.name,
    p.quantity,
    p.low_stock_threshold,
    p.status,
    CASE
        WHEN p.quantity = 0 THEN 'out_of_stock'
        WHEN p.quantity <= p.low_stock_threshold THEN 'low_stock'
        ELSE 'in_stock'
    END AS stock_status,
    (
        SELECT COUNT(*)
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE oi.product_id = p.id
        AND o.status IN ('pending', 'confirmed', 'processing')
    ) AS pending_orders_count
FROM products p;

COMMENT ON VIEW product_stock_status IS 'Products with calculated stock status and pending order count';

-- ============================================================================
-- 8. VIEW FOR LOW-STOCK PRODUCTS
-- ============================================================================
CREATE OR REPLACE VIEW low_stock_products AS
SELECT
    p.id,
    p.farmer_id,
    p.name,
    p.category,
    p.quantity,
    p.low_stock_threshold,
    p.status,
    CASE
        WHEN p.quantity = 0 THEN 'out_of_stock'
        ELSE 'low_stock'
    END AS stock_status
FROM products p
WHERE p.quantity <= p.low_stock_threshold
AND p.status = 'active';

COMMENT ON VIEW low_stock_products IS 'Active products that are low on stock or out of stock';
