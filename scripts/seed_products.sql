-- ============================================================================
-- Mock Products Seed Script for Farm-to-Table Marketplace Demo
-- Run this in Supabase SQL Editor or any PostgreSQL client
-- ============================================================================

-- First, create a test farmer user if not exists
DO $$
DECLARE
    v_farmer_id UUID;
    v_password_hash TEXT := '$2b$12$WkdpLNzVI1DD1.qQ1CWa3er3OuT0Jqh.ETfL3AOrvRlc51VEaMi3m'; -- TestPassword123!
BEGIN
    -- Check if test farmer exists
    SELECT id INTO v_farmer_id FROM users WHERE email = 'testfarmer@example.com';

    IF v_farmer_id IS NULL THEN
        -- Create test farmer
        INSERT INTO users (
            id, email, password_hash, full_name, phone,
            email_verified, role, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            'testfarmer@example.com',
            v_password_hash,
            'Green Valley Farm',
            '+1234567890',
            TRUE,
            'farmer',
            NOW(),
            NOW()
        ) RETURNING id INTO v_farmer_id;

        RAISE NOTICE 'Created test farmer with ID: %', v_farmer_id;

        -- Create farmer profile if table exists
        BEGIN
            INSERT INTO farmers (
                id, user_id, farm_name, farm_description,
                farm_city, farm_state, farm_zip_code,
                farming_practices, profile_completed, created_at, updated_at
            ) VALUES (
                gen_random_uuid(),
                v_farmer_id,
                'Green Valley Farm',
                'A family-owned organic farm dedicated to sustainable agriculture.',
                'Farmville',
                'California',
                '95123',
                ARRAY['Organic', 'Sustainable'],
                TRUE,
                NOW(),
                NOW()
            );
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Farmers table does not exist, skipping profile creation';
        END;
    ELSE
        RAISE NOTICE 'Using existing farmer with ID: %', v_farmer_id;
    END IF;
END $$;

-- Insert mock products using the test farmer
INSERT INTO products (
    id, farmer_id, name, category, description, price, unit,
    quantity, seasonality, images, status, version, low_stock_threshold,
    created_at, updated_at
)
SELECT
    gen_random_uuid(),
    (SELECT id FROM users WHERE email = 'testfarmer@example.com'),
    p.name,
    p.category::product_category,
    p.description,
    p.price,
    p.unit::product_unit,
    p.quantity,
    p.seasonality::seasonality[],
    p.images,
    'active'::product_status,
    1,
    10,
    NOW(),
    NOW()
FROM (VALUES
    -- Vegetables
    ('Organic Tomatoes', 'Vegetables',
     'Vine-ripened organic tomatoes grown without pesticides. Perfect for salads, sandwiches, and cooking.',
     4.99, 'lb', 150, ARRAY['Summer', 'Fall'],
     ARRAY['https://images.unsplash.com/photo-1546470427-227c7c4d0764?w=400']),

    ('Fresh Spinach Bundle', 'Vegetables',
     'Tender baby spinach leaves, freshly harvested. Rich in iron and vitamins.',
     3.49, 'bunch', 75, ARRAY['Spring', 'Fall'],
     ARRAY['https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400']),

    ('Rainbow Carrots', 'Vegetables',
     'Beautiful mix of orange, purple, yellow, and white carrots. Sweet and crunchy.',
     5.99, 'lb', 100, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400']),

    ('Zucchini', 'Vegetables',
     'Fresh green zucchini, perfect for grilling, spiralizing, or baking.',
     2.99, 'lb', 80, ARRAY['Summer'],
     ARRAY['https://images.unsplash.com/photo-1563252722-6434563a985d?w=400']),

    ('Bell Peppers Mix', 'Vegetables',
     'Colorful mix of red, yellow, and orange bell peppers. Sweet and crisp.',
     6.49, 'lb', 60, ARRAY['Summer', 'Fall'],
     ARRAY['https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400']),

    -- Fruits
    ('Honeycrisp Apples', 'Fruits',
     'Crisp and sweet Honeycrisp apples from our orchard. Perfect balance of sweet and tart.',
     6.99, 'lb', 200, ARRAY['Fall', 'Winter'],
     ARRAY['https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400']),

    ('Fresh Strawberries', 'Fruits',
     'Sweet, juicy strawberries picked at peak ripeness. Perfect for desserts or fresh eating.',
     7.99, 'lb', 50, ARRAY['Spring', 'Summer'],
     ARRAY['https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=400']),

    ('Organic Blueberries', 'Fruits',
     'Plump, organic blueberries bursting with antioxidants. Great for breakfast or baking.',
     8.99, 'lb', 40, ARRAY['Summer'],
     ARRAY['https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=400']),

    ('Fresh Peaches', 'Fruits',
     'Tree-ripened peaches with incredible sweetness. Nothing beats a fresh summer peach.',
     5.99, 'lb', 65, ARRAY['Summer'],
     ARRAY['https://images.unsplash.com/photo-1595124216650-1f1c9c3900f7?w=400']),

    -- Dairy
    ('Farm Fresh Milk', 'Dairy',
     'Creamy whole milk from grass-fed cows. Non-homogenized with cream top.',
     5.49, 'each', 30, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400']),

    ('Artisan Cheese Wheel', 'Dairy',
     'Handcrafted aged cheddar cheese. Sharp, creamy, and full of flavor.',
     12.99, 'each', 25, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1452195100486-9cc805987862?w=400']),

    ('Fresh Butter', 'Dairy',
     'Churned fresh butter from grass-fed cream. Rich, golden, and delicious.',
     8.99, 'each', 35, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400']),

    -- Eggs
    ('Free-Range Eggs', 'Eggs',
     'Fresh eggs from happy, free-range chickens. Rich orange yolks with exceptional flavor.',
     6.49, 'dozen', 100, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400']),

    ('Duck Eggs', 'Eggs',
     'Farm-fresh duck eggs with larger, richer yolks. Excellent for baking.',
     9.99, 'dozen', 20, ARRAY['Spring', 'Summer'],
     ARRAY['https://images.unsplash.com/photo-1569288052389-dac9b01c9c05?w=400']),

    -- Honey
    ('Raw Wildflower Honey', 'Honey',
     'Pure, raw wildflower honey from our beehives. Unfiltered and unpasteurized.',
     14.99, 'each', 45, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400']),

    ('Honeycomb', 'Honey',
     'Fresh honeycomb straight from the hive. Delicious with cheese or on toast.',
     18.99, 'each', 15, ARRAY['Summer', 'Fall'],
     ARRAY['https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400']),

    -- Herbs
    ('Fresh Basil', 'Herbs',
     'Aromatic fresh basil, perfect for Italian dishes and pesto.',
     2.99, 'bunch', 60, ARRAY['Summer'],
     ARRAY['https://images.unsplash.com/photo-1527792492728-04de4dd4bc80?w=400']),

    ('Rosemary Sprigs', 'Herbs',
     'Fragrant rosemary for roasting meats and potatoes. A kitchen essential.',
     2.49, 'bunch', 55, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1515586000433-45406d8e6662?w=400']),

    ('Fresh Mint', 'Herbs',
     'Cool, refreshing mint leaves. Perfect for tea, cocktails, and desserts.',
     2.49, 'bunch', 45, ARRAY['Spring', 'Summer'],
     ARRAY['https://images.unsplash.com/photo-1628556270448-4d4e4148e1b1?w=400']),

    -- Meat
    ('Grass-Fed Ground Beef', 'Meat',
     '100% grass-fed and finished ground beef. Lean, flavorful, and ethically raised.',
     11.99, 'lb', 35, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=400']),

    ('Pasture-Raised Chicken', 'Meat',
     'Whole pasture-raised chicken. Tender, flavorful meat from free-roaming chickens.',
     18.99, 'each', 20, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=400']),

    ('Pork Chops', 'Meat',
     'Heritage breed pork chops from pasture-raised pigs. Juicy and full of flavor.',
     14.99, 'lb', 25, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1432139555190-58524dae6a55?w=400']),

    -- Grains
    ('Organic Whole Wheat Flour', 'Grains',
     'Stone-ground whole wheat flour from organic wheat. Perfect for bread and baking.',
     7.99, 'each', 40, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400']),

    ('Heritage Oats', 'Grains',
     'Rolled oats from heritage grain varieties. Nutty flavor for oatmeal and granola.',
     5.99, 'each', 50, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1614961233913-a5113a4a34ed?w=400']),

    -- Low stock items for demo
    ('Heirloom Tomatoes', 'Vegetables',
     'Rare heirloom varieties with incredible flavor. Limited availability!',
     8.99, 'lb', 5, ARRAY['Summer'],
     ARRAY['https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=400']),

    ('Truffle Honey', 'Honey',
     'Luxurious honey infused with black truffle. A gourmet delicacy.',
     29.99, 'each', 3, ARRAY['Year-round'],
     ARRAY['https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400']),

    ('Organic Saffron', 'Herbs',
     'Premium organic saffron threads. The world''s most precious spice.',
     24.99, 'each', 8, ARRAY['Fall'],
     ARRAY['https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400'])

) AS p(name, category, description, price, unit, quantity, seasonality, images)
WHERE NOT EXISTS (
    SELECT 1 FROM products
    WHERE products.name = p.name
    AND products.farmer_id = (SELECT id FROM users WHERE email = 'testfarmer@example.com')
);

-- Show summary
SELECT
    'Products seeded successfully!' AS status,
    COUNT(*) AS total_products,
    (SELECT full_name FROM users WHERE email = 'testfarmer@example.com') AS farmer_name
FROM products
WHERE farmer_id = (SELECT id FROM users WHERE email = 'testfarmer@example.com');
