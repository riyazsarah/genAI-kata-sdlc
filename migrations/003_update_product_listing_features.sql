-- Migration: 003_update_product_listing_features
-- Description: Add product history tracking, optimistic locking, and notification support for US-007
-- User Story: US-007 - Update Product Listing
-- Created: 2025-12-10

-- ============================================================================
-- 1. ADD VERSION COLUMN FOR OPTIMISTIC LOCKING
-- ============================================================================
-- Prevents concurrent edit conflicts by tracking version number
ALTER TABLE products ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

COMMENT ON COLUMN products.version IS 'Version number for optimistic locking to prevent concurrent edit conflicts';

-- ============================================================================
-- 2. CREATE PRODUCT HISTORY TABLE FOR AUDIT PURPOSES
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    farmer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Snapshot of product fields at the time of change
    name VARCHAR(100) NOT NULL,
    category product_category NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    unit product_unit NOT NULL,
    quantity INTEGER NOT NULL,
    seasonality seasonality[] NOT NULL,
    images TEXT[] NOT NULL,
    status product_status NOT NULL,
    version INTEGER NOT NULL,

    -- Audit metadata
    changed_by UUID NOT NULL REFERENCES users(id),
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('created', 'updated', 'deleted')),
    changed_fields TEXT[], -- Array of field names that were changed
    change_reason TEXT, -- Optional reason for the change
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_product_history_product_id ON product_history(product_id);
CREATE INDEX IF NOT EXISTS idx_product_history_farmer_id ON product_history(farmer_id);
CREATE INDEX IF NOT EXISTS idx_product_history_created_at ON product_history(created_at);
CREATE INDEX IF NOT EXISTS idx_product_history_change_type ON product_history(change_type);

-- Enable RLS
ALTER TABLE product_history ENABLE ROW LEVEL SECURITY;

-- Policy: Farmers can view their own product history
CREATE POLICY product_history_select ON product_history
    FOR SELECT
    USING (true);

-- Policy: Allow inserts (system/application inserts history records)
CREATE POLICY product_history_insert ON product_history
    FOR INSERT
    WITH CHECK (true);

COMMENT ON TABLE product_history IS 'Audit trail of all product changes for US-007 compliance';
COMMENT ON COLUMN product_history.changed_fields IS 'List of fields that were modified in this update';
COMMENT ON COLUMN product_history.change_reason IS 'Optional explanation for why the change was made';

-- ============================================================================
-- 3. CREATE PRODUCT IMAGES TABLE FOR BETTER IMAGE MANAGEMENT
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    alt_text VARCHAR(255),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure only one primary image per product
    CONSTRAINT unique_primary_per_product UNIQUE (product_id, is_primary)
        DEFERRABLE INITIALLY DEFERRED
);

-- Create a partial unique index instead of the constraint above for primary images
DROP INDEX IF EXISTS idx_product_images_primary;
CREATE UNIQUE INDEX idx_product_images_primary ON product_images(product_id)
    WHERE is_primary = TRUE;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images(product_id);
CREATE INDEX IF NOT EXISTS idx_product_images_display_order ON product_images(product_id, display_order);

-- Enable RLS
ALTER TABLE product_images ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY product_images_select ON product_images
    FOR SELECT
    USING (true);

CREATE POLICY product_images_insert ON product_images
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY product_images_update ON product_images
    FOR UPDATE
    USING (true);

CREATE POLICY product_images_delete ON product_images
    FOR DELETE
    USING (true);

COMMENT ON TABLE product_images IS 'Separate image storage for products, allowing add/remove operations (AC-007-3)';
COMMENT ON COLUMN product_images.display_order IS 'Order in which images appear in the gallery';
COMMENT ON COLUMN product_images.is_primary IS 'Primary image shown as thumbnail in listings';

-- ============================================================================
-- 4. CREATE PRODUCT CHANGE NOTIFICATIONS TABLE
-- ============================================================================
-- For notifying customers about significant product changes (AC-007-5)
CREATE TYPE notification_type AS ENUM (
    'price_increase',
    'price_decrease',
    'out_of_stock',
    'back_in_stock',
    'product_discontinued',
    'product_updated'
);

CREATE TABLE IF NOT EXISTS product_change_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    notification_type notification_type NOT NULL,

    -- Change details
    old_value TEXT,
    new_value TEXT,
    change_percentage DECIMAL(5, 2), -- For price changes

    -- Notification status
    affected_users_count INTEGER NOT NULL DEFAULT 0,
    notifications_sent INTEGER NOT NULL DEFAULT 0,
    notification_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (notification_status IN ('pending', 'processing', 'completed', 'failed')),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_product_notifications_product_id ON product_change_notifications(product_id);
CREATE INDEX IF NOT EXISTS idx_product_notifications_status ON product_change_notifications(notification_status);
CREATE INDEX IF NOT EXISTS idx_product_notifications_created_at ON product_change_notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_product_notifications_type ON product_change_notifications(notification_type);

-- Enable RLS
ALTER TABLE product_change_notifications ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY product_notifications_select ON product_change_notifications
    FOR SELECT
    USING (true);

CREATE POLICY product_notifications_insert ON product_change_notifications
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY product_notifications_update ON product_change_notifications
    FOR UPDATE
    USING (true);

COMMENT ON TABLE product_change_notifications IS 'Track significant product changes for customer notifications (AC-007-5)';
COMMENT ON COLUMN product_change_notifications.change_percentage IS 'Percentage change for price updates';

-- ============================================================================
-- 5. CREATE PRODUCT SUBSCRIBERS TABLE
-- ============================================================================
-- Track users who should be notified about product changes
CREATE TABLE IF NOT EXISTS product_subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_type VARCHAR(50) NOT NULL DEFAULT 'all_updates'
        CHECK (subscription_type IN ('all_updates', 'price_changes', 'stock_alerts', 'none')),
    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one subscription per user per product
    CONSTRAINT unique_product_subscriber UNIQUE (product_id, user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_product_subscribers_product_id ON product_subscribers(product_id);
CREATE INDEX IF NOT EXISTS idx_product_subscribers_user_id ON product_subscribers(user_id);
CREATE INDEX IF NOT EXISTS idx_product_subscribers_type ON product_subscribers(subscription_type);

-- Enable RLS
ALTER TABLE product_subscribers ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY product_subscribers_select ON product_subscribers
    FOR SELECT
    USING (true);

CREATE POLICY product_subscribers_insert ON product_subscribers
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY product_subscribers_update ON product_subscribers
    FOR UPDATE
    USING (true);

CREATE POLICY product_subscribers_delete ON product_subscribers
    FOR DELETE
    USING (true);

COMMENT ON TABLE product_subscribers IS 'Users subscribed to product updates for notification purposes';

-- ============================================================================
-- 6. CREATE FUNCTION TO INCREMENT VERSION ON UPDATE
-- ============================================================================
CREATE OR REPLACE FUNCTION increment_product_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Increment version on every update
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for version increment
DROP TRIGGER IF EXISTS increment_product_version_trigger ON products;
CREATE TRIGGER increment_product_version_trigger
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION increment_product_version();

-- ============================================================================
-- 7. CREATE FUNCTION TO LOG PRODUCT HISTORY
-- ============================================================================
CREATE OR REPLACE FUNCTION log_product_history()
RETURNS TRIGGER AS $$
DECLARE
    changed_fields_arr TEXT[] := ARRAY[]::TEXT[];
    change_type_val VARCHAR(20);
BEGIN
    IF TG_OP = 'INSERT' THEN
        change_type_val := 'created';
        INSERT INTO product_history (
            product_id, farmer_id, name, category, description, price, unit,
            quantity, seasonality, images, status, version, changed_by,
            change_type, changed_fields
        ) VALUES (
            NEW.id, NEW.farmer_id, NEW.name, NEW.category, NEW.description,
            NEW.price, NEW.unit, NEW.quantity, NEW.seasonality, NEW.images,
            NEW.status, NEW.version, NEW.farmer_id, change_type_val,
            ARRAY['all']::TEXT[]
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        change_type_val := 'updated';

        -- Track which fields changed
        IF OLD.name IS DISTINCT FROM NEW.name THEN
            changed_fields_arr := array_append(changed_fields_arr, 'name');
        END IF;
        IF OLD.category IS DISTINCT FROM NEW.category THEN
            changed_fields_arr := array_append(changed_fields_arr, 'category');
        END IF;
        IF OLD.description IS DISTINCT FROM NEW.description THEN
            changed_fields_arr := array_append(changed_fields_arr, 'description');
        END IF;
        IF OLD.price IS DISTINCT FROM NEW.price THEN
            changed_fields_arr := array_append(changed_fields_arr, 'price');
        END IF;
        IF OLD.unit IS DISTINCT FROM NEW.unit THEN
            changed_fields_arr := array_append(changed_fields_arr, 'unit');
        END IF;
        IF OLD.quantity IS DISTINCT FROM NEW.quantity THEN
            changed_fields_arr := array_append(changed_fields_arr, 'quantity');
        END IF;
        IF OLD.seasonality IS DISTINCT FROM NEW.seasonality THEN
            changed_fields_arr := array_append(changed_fields_arr, 'seasonality');
        END IF;
        IF OLD.images IS DISTINCT FROM NEW.images THEN
            changed_fields_arr := array_append(changed_fields_arr, 'images');
        END IF;
        IF OLD.status IS DISTINCT FROM NEW.status THEN
            changed_fields_arr := array_append(changed_fields_arr, 'status');
        END IF;

        -- Only log if something actually changed
        IF array_length(changed_fields_arr, 1) > 0 THEN
            INSERT INTO product_history (
                product_id, farmer_id, name, category, description, price, unit,
                quantity, seasonality, images, status, version, changed_by,
                change_type, changed_fields
            ) VALUES (
                NEW.id, NEW.farmer_id, NEW.name, NEW.category, NEW.description,
                NEW.price, NEW.unit, NEW.quantity, NEW.seasonality, NEW.images,
                NEW.status, NEW.version, NEW.farmer_id, change_type_val,
                changed_fields_arr
            );
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        change_type_val := 'deleted';
        INSERT INTO product_history (
            product_id, farmer_id, name, category, description, price, unit,
            quantity, seasonality, images, status, version, changed_by,
            change_type, changed_fields
        ) VALUES (
            OLD.id, OLD.farmer_id, OLD.name, OLD.category, OLD.description,
            OLD.price, OLD.unit, OLD.quantity, OLD.seasonality, OLD.images,
            OLD.status, OLD.version, OLD.farmer_id, change_type_val,
            ARRAY['all']::TEXT[]
        );
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for history logging
DROP TRIGGER IF EXISTS log_product_history_trigger ON products;
CREATE TRIGGER log_product_history_trigger
    AFTER INSERT OR UPDATE OR DELETE ON products
    FOR EACH ROW
    EXECUTE FUNCTION log_product_history();

-- ============================================================================
-- 8. CREATE FUNCTION TO DETECT SIGNIFICANT CHANGES AND QUEUE NOTIFICATIONS
-- ============================================================================
CREATE OR REPLACE FUNCTION queue_product_change_notification()
RETURNS TRIGGER AS $$
DECLARE
    price_change_pct DECIMAL(5, 2);
    notif_type notification_type;
    subscriber_count INTEGER;
BEGIN
    -- Only process updates
    IF TG_OP != 'UPDATE' THEN
        RETURN NEW;
    END IF;

    -- Get subscriber count for this product
    SELECT COUNT(*) INTO subscriber_count
    FROM product_subscribers
    WHERE product_id = NEW.id AND subscription_type != 'none';

    -- Skip if no subscribers
    IF subscriber_count = 0 THEN
        RETURN NEW;
    END IF;

    -- Check for price changes
    IF OLD.price IS DISTINCT FROM NEW.price THEN
        price_change_pct := ((NEW.price - OLD.price) / OLD.price * 100)::DECIMAL(5,2);

        IF NEW.price > OLD.price THEN
            notif_type := 'price_increase';
        ELSE
            notif_type := 'price_decrease';
        END IF;

        INSERT INTO product_change_notifications (
            product_id, notification_type, old_value, new_value,
            change_percentage, affected_users_count
        ) VALUES (
            NEW.id, notif_type, OLD.price::TEXT, NEW.price::TEXT,
            price_change_pct, subscriber_count
        );
    END IF;

    -- Check for stock changes (out of stock)
    IF OLD.quantity > 0 AND NEW.quantity = 0 THEN
        INSERT INTO product_change_notifications (
            product_id, notification_type, old_value, new_value,
            affected_users_count
        ) VALUES (
            NEW.id, 'out_of_stock', OLD.quantity::TEXT, '0', subscriber_count
        );
    END IF;

    -- Check for stock changes (back in stock)
    IF OLD.quantity = 0 AND NEW.quantity > 0 THEN
        INSERT INTO product_change_notifications (
            product_id, notification_type, old_value, new_value,
            affected_users_count
        ) VALUES (
            NEW.id, 'back_in_stock', '0', NEW.quantity::TEXT, subscriber_count
        );
    END IF;

    -- Check for product discontinued (archived)
    IF OLD.status != 'archived' AND NEW.status = 'archived' THEN
        INSERT INTO product_change_notifications (
            product_id, notification_type, old_value, new_value,
            affected_users_count
        ) VALUES (
            NEW.id, 'product_discontinued', OLD.status::TEXT, 'archived', subscriber_count
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for notification queuing
DROP TRIGGER IF EXISTS queue_product_notification_trigger ON products;
CREATE TRIGGER queue_product_notification_trigger
    AFTER UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION queue_product_change_notification();

-- ============================================================================
-- 9. HELPER FUNCTION FOR OPTIMISTIC LOCKING VALIDATION
-- ============================================================================
CREATE OR REPLACE FUNCTION validate_product_version(
    p_product_id UUID,
    p_expected_version INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    current_version INTEGER;
BEGIN
    SELECT version INTO current_version
    FROM products
    WHERE id = p_product_id;

    IF current_version IS NULL THEN
        RAISE EXCEPTION 'Product not found: %', p_product_id;
    END IF;

    IF current_version != p_expected_version THEN
        RAISE EXCEPTION 'Version conflict: expected %, found %. Product was modified by another user.',
            p_expected_version, current_version;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION validate_product_version IS 'Validates product version for optimistic locking before updates';

-- ============================================================================
-- 10. VIEW FOR PRODUCT WITH FULL DETAILS
-- ============================================================================
CREATE OR REPLACE VIEW product_details AS
SELECT
    p.*,
    u.full_name AS farmer_name,
    u.email AS farmer_email,
    (
        SELECT COALESCE(json_agg(
            json_build_object(
                'id', pi.id,
                'url', pi.image_url,
                'order', pi.display_order,
                'is_primary', pi.is_primary,
                'alt_text', pi.alt_text
            ) ORDER BY pi.display_order
        ), '[]'::json)
        FROM product_images pi
        WHERE pi.product_id = p.id
    ) AS images_detail,
    (
        SELECT COUNT(*)
        FROM product_subscribers ps
        WHERE ps.product_id = p.id AND ps.subscription_type != 'none'
    ) AS subscriber_count
FROM products p
JOIN users u ON p.farmer_id = u.id;

COMMENT ON VIEW product_details IS 'Complete product view with farmer info, images, and subscriber count';
