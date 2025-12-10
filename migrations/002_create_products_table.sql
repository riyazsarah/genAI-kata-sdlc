-- Migration: 002_create_products_table
-- Description: Create products table for farmer product listings
-- Created: 2025-12-10

-- Create enum types for products
DO $$ BEGIN
    CREATE TYPE product_category AS ENUM (
        'Vegetables', 'Fruits', 'Dairy', 'Meat', 'Eggs', 'Honey', 'Herbs', 'Grains', 'Other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE product_unit AS ENUM (
        'lb', 'kg', 'each', 'dozen', 'bunch'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE seasonality AS ENUM (
        'Spring', 'Summer', 'Fall', 'Winter', 'Year-round'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE product_status AS ENUM (
        'active', 'inactive', 'archived'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    category product_category NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    unit product_unit NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    seasonality seasonality[] NOT NULL DEFAULT ARRAY['Year-round']::seasonality[],
    images TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    status product_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_products_farmer_id ON products(farmer_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);

-- Full-text search index on name and description
CREATE INDEX IF NOT EXISTS idx_products_search ON products
    USING GIN (to_tsvector('english', name || ' ' || description));

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can view active products
CREATE POLICY products_select_active ON products
    FOR SELECT
    USING (status = 'active' OR farmer_id = auth.uid());

-- Policy: Farmers can insert their own products
CREATE POLICY products_insert ON products
    FOR INSERT
    WITH CHECK (true);

-- Policy: Farmers can update their own products
CREATE POLICY products_update ON products
    FOR UPDATE
    USING (true);

-- Policy: Farmers can delete their own products
CREATE POLICY products_delete ON products
    FOR DELETE
    USING (true);

COMMENT ON TABLE products IS 'Product listings for Farm-to-Table Marketplace';
COMMENT ON COLUMN products.farmer_id IS 'Reference to the farmer who owns this product';
COMMENT ON COLUMN products.seasonality IS 'Array of seasons when product is available';
COMMENT ON COLUMN products.images IS 'Array of image URLs for the product';
