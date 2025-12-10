"""
Seed script to add mock products to the database.

Usage:
    uv run python scripts/seed_products.py

This script will:
1. Find or create a test farmer user
2. Insert sample products across different categories
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Sample product data
MOCK_PRODUCTS = [
    # Vegetables
    {
        "name": "Organic Tomatoes",
        "category": "Vegetables",
        "description": "Vine-ripened organic tomatoes grown without pesticides. Perfect for salads, sandwiches, and cooking. Our tomatoes are harvested at peak ripeness for maximum flavor.",
        "price": 4.99,
        "unit": "lb",
        "quantity": 150,
        "seasonality": ["Summer", "Fall"],
        "images": ["https://images.unsplash.com/photo-1546470427-227c7c4d0764?w=400"],
    },
    {
        "name": "Fresh Spinach Bundle",
        "category": "Vegetables",
        "description": "Tender baby spinach leaves, freshly harvested. Rich in iron and vitamins. Great for salads, smoothies, or sauteed dishes.",
        "price": 3.49,
        "unit": "bunch",
        "quantity": 75,
        "seasonality": ["Spring", "Fall"],
        "images": ["https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400"],
    },
    {
        "name": "Rainbow Carrots",
        "category": "Vegetables",
        "description": "Beautiful mix of orange, purple, yellow, and white carrots. Sweet and crunchy, perfect for roasting or eating raw.",
        "price": 5.99,
        "unit": "lb",
        "quantity": 100,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400"],
    },
    {
        "name": "Zucchini",
        "category": "Vegetables",
        "description": "Fresh green zucchini, perfect for grilling, spiralizing, or baking into bread. Tender and versatile.",
        "price": 2.99,
        "unit": "lb",
        "quantity": 80,
        "seasonality": ["Summer"],
        "images": ["https://images.unsplash.com/photo-1563252722-6434563a985d?w=400"],
    },
    # Fruits
    {
        "name": "Honeycrisp Apples",
        "category": "Fruits",
        "description": "Crisp and sweet Honeycrisp apples from our orchard. The perfect balance of sweet and tart. Excellent for snacking or baking.",
        "price": 6.99,
        "unit": "lb",
        "quantity": 200,
        "seasonality": ["Fall", "Winter"],
        "images": ["https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400"],
    },
    {
        "name": "Fresh Strawberries",
        "category": "Fruits",
        "description": "Sweet, juicy strawberries picked at the peak of ripeness. Perfect for desserts, smoothies, or eating fresh.",
        "price": 7.99,
        "unit": "lb",
        "quantity": 50,
        "seasonality": ["Spring", "Summer"],
        "images": ["https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=400"],
    },
    {
        "name": "Organic Blueberries",
        "category": "Fruits",
        "description": "Plump, organic blueberries bursting with antioxidants. Great for breakfast, baking, or freezing for later.",
        "price": 8.99,
        "unit": "lb",
        "quantity": 40,
        "seasonality": ["Summer"],
        "images": ["https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=400"],
    },
    # Dairy
    {
        "name": "Farm Fresh Milk",
        "category": "Dairy",
        "description": "Creamy whole milk from grass-fed cows. Non-homogenized with cream top. Rich in nutrients and amazing taste.",
        "price": 5.49,
        "unit": "each",
        "quantity": 30,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400"],
    },
    {
        "name": "Artisan Cheese Wheel",
        "category": "Dairy",
        "description": "Handcrafted aged cheddar cheese. Sharp, creamy, and full of flavor. Made with milk from our own dairy cows.",
        "price": 12.99,
        "unit": "each",
        "quantity": 25,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1452195100486-9cc805987862?w=400"],
    },
    # Eggs
    {
        "name": "Free-Range Eggs",
        "category": "Eggs",
        "description": "Fresh eggs from happy, free-range chickens. Rich orange yolks with exceptional flavor. Perfect for any meal.",
        "price": 6.49,
        "unit": "dozen",
        "quantity": 100,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400"],
    },
    {
        "name": "Duck Eggs",
        "category": "Eggs",
        "description": "Farm-fresh duck eggs with larger, richer yolks. Excellent for baking and gourmet cooking.",
        "price": 9.99,
        "unit": "dozen",
        "quantity": 20,
        "seasonality": ["Spring", "Summer"],
        "images": ["https://images.unsplash.com/photo-1569288052389-dac9b01c9c05?w=400"],
    },
    # Honey
    {
        "name": "Raw Wildflower Honey",
        "category": "Honey",
        "description": "Pure, raw wildflower honey from our own beehives. Unfiltered and unpasteurized for maximum health benefits.",
        "price": 14.99,
        "unit": "each",
        "quantity": 45,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400"],
    },
    {
        "name": "Honeycomb",
        "category": "Honey",
        "description": "Fresh honeycomb straight from the hive. A delicious treat to spread on toast or enjoy with cheese.",
        "price": 18.99,
        "unit": "each",
        "quantity": 15,
        "seasonality": ["Summer", "Fall"],
        "images": ["https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400"],
    },
    # Herbs
    {
        "name": "Fresh Basil",
        "category": "Herbs",
        "description": "Aromatic fresh basil, perfect for Italian dishes, pesto, and summer salads. Grown without pesticides.",
        "price": 2.99,
        "unit": "bunch",
        "quantity": 60,
        "seasonality": ["Summer"],
        "images": ["https://images.unsplash.com/photo-1527792492728-04de4dd4bc80?w=400"],
    },
    {
        "name": "Rosemary Sprigs",
        "category": "Herbs",
        "description": "Fragrant rosemary sprigs for roasting meats, potatoes, and bread. A kitchen essential.",
        "price": 2.49,
        "unit": "bunch",
        "quantity": 55,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1515586000433-45406d8e6662?w=400"],
    },
    # Meat
    {
        "name": "Grass-Fed Ground Beef",
        "category": "Meat",
        "description": "100% grass-fed and finished ground beef. Lean, flavorful, and ethically raised on our pastures.",
        "price": 11.99,
        "unit": "lb",
        "quantity": 35,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=400"],
    },
    {
        "name": "Pasture-Raised Chicken",
        "category": "Meat",
        "description": "Whole pasture-raised chicken. Tender, flavorful meat from chickens raised outdoors with space to roam.",
        "price": 18.99,
        "unit": "each",
        "quantity": 20,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=400"],
    },
    # Grains
    {
        "name": "Organic Whole Wheat Flour",
        "category": "Grains",
        "description": "Stone-ground whole wheat flour from our organic wheat fields. Perfect for bread, pasta, and baking.",
        "price": 7.99,
        "unit": "each",
        "quantity": 40,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400"],
    },
    {
        "name": "Heritage Oats",
        "category": "Grains",
        "description": "Rolled oats from heritage grain varieties. Nutty flavor perfect for oatmeal, granola, and baking.",
        "price": 5.99,
        "unit": "each",
        "quantity": 50,
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1614961233913-a5113a4a34ed?w=400"],
    },
    # Low stock items for testing
    {
        "name": "Organic Heirloom Tomatoes",
        "category": "Vegetables",
        "description": "Rare heirloom tomato varieties with incredible flavor. Limited availability - get them while they last!",
        "price": 8.99,
        "unit": "lb",
        "quantity": 5,  # Low stock
        "seasonality": ["Summer"],
        "images": ["https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=400"],
    },
    {
        "name": "Truffle Honey",
        "category": "Honey",
        "description": "Luxurious honey infused with black truffle. A gourmet delicacy for special occasions.",
        "price": 29.99,
        "unit": "each",
        "quantity": 3,  # Low stock
        "seasonality": ["Year-round"],
        "images": ["https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400"],
    },
]


def get_or_create_test_farmer():
    """Get existing test farmer or create a new one."""
    test_email = "testfarmer@example.com"

    # Check if test farmer exists
    result = supabase.table("users").select("*").eq("email", test_email).execute()

    if result.data:
        farmer = result.data[0]
        print(f"Found existing test farmer: {farmer['full_name']} ({farmer['id']})")
        return farmer["id"]

    # Create test farmer
    import bcrypt

    password_hash = bcrypt.hashpw("TestPassword123!".encode(), bcrypt.gensalt()).decode()

    farmer_data = {
        "id": str(uuid4()),
        "email": test_email,
        "password_hash": password_hash,
        "full_name": "Green Valley Farm",
        "phone": "+1234567890",
        "email_verified": True,
        "role": "farmer",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    result = supabase.table("users").insert(farmer_data).execute()

    if result.data:
        farmer_id = result.data[0]["id"]
        print(f"Created test farmer: Green Valley Farm ({farmer_id})")

        # Create farmer profile
        farmer_profile = {
            "id": str(uuid4()),
            "user_id": farmer_id,
            "farm_name": "Green Valley Farm",
            "farm_description": "A family-owned organic farm dedicated to sustainable agriculture and providing the freshest produce to our community.",
            "farm_city": "Farmville",
            "farm_state": "California",
            "farm_zip_code": "95123",
            "farming_practices": ["Organic", "Sustainable"],
            "profile_completed": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        try:
            supabase.table("farmers").insert(farmer_profile).execute()
            print("Created farmer profile")
        except Exception as e:
            print(f"Note: Could not create farmer profile (table may not exist): {e}")

        return farmer_id

    print("Error: Could not create test farmer")
    sys.exit(1)


def seed_products(farmer_id: str):
    """Insert mock products into the database."""
    print(f"\nSeeding {len(MOCK_PRODUCTS)} products...")

    success_count = 0
    error_count = 0

    for product_data in MOCK_PRODUCTS:
        try:
            product = {
                "id": str(uuid4()),
                "farmer_id": farmer_id,
                "name": product_data["name"],
                "category": product_data["category"],
                "description": product_data["description"],
                "price": product_data["price"],
                "unit": product_data["unit"],
                "quantity": product_data["quantity"],
                "seasonality": product_data["seasonality"],
                "images": product_data.get("images", []),
                "status": "active",
                "version": 1,
                "low_stock_threshold": 10,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = supabase.table("products").insert(product).execute()

            if result.data:
                print(f"  + {product_data['name']}")
                success_count += 1
            else:
                print(f"  ! Failed to insert: {product_data['name']}")
                error_count += 1

        except Exception as e:
            print(f"  ! Error inserting {product_data['name']}: {e}")
            error_count += 1

    print(f"\nSeed complete: {success_count} products added, {error_count} errors")


def clear_existing_products(farmer_id: str):
    """Optionally clear existing products for the test farmer."""
    result = supabase.table("products").delete().eq("farmer_id", farmer_id).execute()
    if result.data:
        print(f"Cleared {len(result.data)} existing products")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed mock products to database")
    parser.add_argument("--clear", action="store_true", help="Clear existing products first")
    args = parser.parse_args()

    print("=" * 50)
    print("Farm-to-Table Product Seeder")
    print("=" * 50)

    # Get or create test farmer
    farmer_id = get_or_create_test_farmer()

    # Optionally clear existing products
    if args.clear:
        clear_existing_products(farmer_id)

    # Seed products
    seed_products(farmer_id)

    print("\nDone!")
    print(f"Test farmer email: testfarmer@example.com")
    print(f"Test farmer password: TestPassword123!")


if __name__ == "__main__":
    main()
