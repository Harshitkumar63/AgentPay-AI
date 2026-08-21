"""Seed script — creates demo merchant, products, and policies."""

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.policy import Policy


DEMO_MERCHANT = {
    "id": "merchant_001",
    "name": "UrbanCart",
    "email": "hello@urbancart.demo",
    "description": "Modern lifestyle products for urban professionals",
    "currency": "INR",
}

DEMO_PRODUCTS = [
    # ── Shoes ──
    {
        "id": "prod_001", "name": "ProRunner X1 Running Shoes", "slug": "prorunner-x1-running-shoes",
        "description": "Lightweight running shoes with responsive cushioning and breathable mesh upper. Perfect for daily runs and marathons. Available in black and blue.",
        "category": "shoes", "price": 2499, "stock": 25,
        "image_url": "/images/running-shoes.jpg",
        "tags": ["running", "sports", "shoes", "black", "blue", "fitness"],
        "metadata_extra": {"colors": ["black", "blue"], "sizes": [7, 8, 9, 10, 11], "brand": "ProRunner",
                           "cross_sell": ["prod_002", "prod_003"], "upsell": "prod_004"},
    },
    {
        "id": "prod_002", "name": "Performance Running Socks (3-Pack)", "slug": "performance-running-socks",
        "description": "Moisture-wicking athletic socks with arch support and cushioned sole. Ideal companion for running shoes.",
        "category": "accessories", "price": 399, "stock": 100,
        "image_url": "/images/running-socks.jpg",
        "tags": ["running", "socks", "accessories", "fitness"],
        "metadata_extra": {"colors": ["white", "black"], "sizes": ["M", "L"], "brand": "ProRunner",
                           "cross_sell": ["prod_001", "prod_003"]},
    },
    {
        "id": "prod_003", "name": "HydroFlask Sports Bottle 750ml", "slug": "hydroflask-sports-bottle",
        "description": "Insulated stainless steel sports bottle. Keeps water cold for 24 hours. Leak-proof design.",
        "category": "fitness", "price": 899, "stock": 50,
        "image_url": "/images/sports-bottle.jpg",
        "tags": ["fitness", "bottle", "sports", "hydration"],
        "metadata_extra": {"colors": ["black", "blue", "red"], "capacity": "750ml",
                           "cross_sell": ["prod_001", "prod_005"]},
    },
    {
        "id": "prod_004", "name": "ProRunner Elite Racing Shoes", "slug": "prorunner-elite-racing-shoes",
        "description": "Premium carbon-plated racing shoes with energy-return technology. For serious runners who want maximum performance.",
        "category": "shoes", "price": 4999, "stock": 10,
        "image_url": "/images/elite-shoes.jpg",
        "tags": ["running", "racing", "shoes", "premium", "black", "white"],
        "metadata_extra": {"colors": ["black", "white"], "sizes": [7, 8, 9, 10, 11], "brand": "ProRunner",
                           "cross_sell": ["prod_002", "prod_003"], "upsell_from": "prod_001"},
    },
    # ── Electronics ──
    {
        "id": "prod_005", "name": "SwiftBook Pro 14\" Laptop", "slug": "swiftbook-pro-14-laptop",
        "description": "Powerful ultrabook with 14-inch IPS display, 16GB RAM, 512GB SSD, and all-day battery life. Perfect for professionals.",
        "category": "electronics", "price": 49999, "stock": 8,
        "image_url": "/images/laptop.jpg",
        "tags": ["laptop", "electronics", "ultrabook", "work"],
        "metadata_extra": {"brand": "SwiftBook", "ram": "16GB", "storage": "512GB SSD",
                           "cross_sell": ["prod_006", "prod_007"]},
    },
    {
        "id": "prod_006", "name": "Urban Laptop Sleeve 14\"", "slug": "urban-laptop-sleeve",
        "description": "Water-resistant neoprene laptop sleeve with cushioned interior. Fits 13-14 inch laptops perfectly.",
        "category": "bags", "price": 1299, "stock": 30,
        "image_url": "/images/laptop-bag.jpg",
        "tags": ["bag", "laptop", "accessories", "sleeve"],
        "metadata_extra": {"colors": ["grey", "black", "navy"], "fits": "13-14 inch",
                           "cross_sell": ["prod_005", "prod_007"]},
    },
    {
        "id": "prod_007", "name": "ErgoClick Wireless Mouse", "slug": "ergoclick-wireless-mouse",
        "description": "Ergonomic wireless mouse with silent clicks, adjustable DPI, and USB-C charging. 6-month battery life.",
        "category": "electronics", "price": 799, "stock": 40,
        "image_url": "/images/wireless-mouse.jpg",
        "tags": ["mouse", "wireless", "electronics", "accessories", "ergonomic"],
        "metadata_extra": {"colors": ["black", "white", "grey"], "connectivity": "Bluetooth + USB",
                           "cross_sell": ["prod_005", "prod_006"]},
    },
    # ── Phone & Accessories ──
    {
        "id": "prod_008", "name": "NovaPhone 12 Pro", "slug": "novaphone-12-pro",
        "description": "Flagship smartphone with 6.7-inch AMOLED display, 108MP camera, 5G connectivity, and 5000mAh battery.",
        "category": "electronics", "price": 34999, "stock": 12,
        "image_url": "/images/phone.jpg",
        "tags": ["phone", "smartphone", "electronics", "5G"],
        "metadata_extra": {"brand": "Nova", "storage": "256GB", "camera": "108MP",
                           "cross_sell": ["prod_009", "prod_010"]},
    },
    {
        "id": "prod_009", "name": "NovaPhone 12 Pro Clear Case", "slug": "novaphone-12-pro-case",
        "description": "Crystal-clear protective case with shock-absorbent corners. Shows off your phone's design while keeping it safe.",
        "category": "accessories", "price": 499, "stock": 60,
        "image_url": "/images/phone-case.jpg",
        "tags": ["case", "phone", "accessories", "protection"],
        "metadata_extra": {"colors": ["clear", "frosted"], "compatible": "NovaPhone 12 Pro",
                           "cross_sell": ["prod_008", "prod_010"]},
    },
    {
        "id": "prod_010", "name": "UltraShield Tempered Glass Screen Protector", "slug": "ultrashield-screen-protector",
        "description": "9H hardness tempered glass screen protector with oleophobic coating. Anti-fingerprint and scratch-resistant.",
        "category": "accessories", "price": 299, "stock": 80,
        "image_url": "/images/screen-protector.jpg",
        "tags": ["screen-protector", "phone", "accessories", "protection"],
        "metadata_extra": {"compatible": "NovaPhone 12 Pro", "hardness": "9H",
                           "cross_sell": ["prod_008", "prod_009"]},
    },
    # ── Bags ──
    {
        "id": "prod_011", "name": "UrbanPack Commuter Backpack", "slug": "urbanpack-commuter-backpack",
        "description": "Sleek urban backpack with laptop compartment, USB charging port, and water-resistant fabric. 25L capacity.",
        "category": "bags", "price": 1899, "stock": 20,
        "image_url": "/images/backpack.jpg",
        "tags": ["backpack", "bag", "urban", "commuter", "black"],
        "metadata_extra": {"colors": ["black", "grey", "navy"], "capacity": "25L",
                           "cross_sell": ["prod_005", "prod_012"], "upsell": "prod_013"},
    },
    {
        "id": "prod_012", "name": "Compact Travel Organizer", "slug": "compact-travel-organizer",
        "description": "Multi-pocket electronics organizer for cables, chargers, and accessories. Essential travel companion.",
        "category": "accessories", "price": 599, "stock": 45,
        "image_url": "/images/organizer.jpg",
        "tags": ["organizer", "travel", "accessories", "electronics"],
        "metadata_extra": {"colors": ["black", "grey"],
                           "cross_sell": ["prod_011", "prod_005"]},
    },
    {
        "id": "prod_013", "name": "UrbanPack Pro Travel Backpack", "slug": "urbanpack-pro-travel-backpack",
        "description": "Premium expandable travel backpack with TSA-approved laptop compartment, anti-theft zippers, and 40L capacity. The ultimate travel companion.",
        "category": "bags", "price": 3499, "stock": 15,
        "image_url": "/images/travel-backpack.jpg",
        "tags": ["backpack", "bag", "travel", "premium", "black"],
        "metadata_extra": {"colors": ["black", "olive"], "capacity": "40L", "upsell_from": "prod_011",
                           "cross_sell": ["prod_012"]},
    },
    # ── Fitness ──
    {
        "id": "prod_014", "name": "FlexBand Resistance Set (5-Pack)", "slug": "flexband-resistance-set",
        "description": "Set of 5 resistance bands with varying intensity levels. Includes carry bag and exercise guide. Great for home workouts.",
        "category": "fitness", "price": 699, "stock": 35,
        "image_url": "/images/resistance-bands.jpg",
        "tags": ["fitness", "workout", "resistance", "home-gym"],
        "metadata_extra": {"levels": ["Light", "Medium", "Heavy", "X-Heavy", "XX-Heavy"],
                           "cross_sell": ["prod_015", "prod_003"]},
    },
    {
        "id": "prod_015", "name": "ProGrip Yoga Mat (6mm)", "slug": "progrip-yoga-mat",
        "description": "Non-slip yoga mat with alignment lines, 6mm thickness for joint comfort. Eco-friendly TPE material.",
        "category": "fitness", "price": 1299, "stock": 25,
        "image_url": "/images/yoga-mat.jpg",
        "tags": ["fitness", "yoga", "mat", "workout"],
        "metadata_extra": {"colors": ["purple", "blue", "black"], "thickness": "6mm",
                           "cross_sell": ["prod_014", "prod_003"]},
    },
    # ── Clothing ──
    {
        "id": "prod_016", "name": "DryFit Performance T-Shirt", "slug": "dryfit-performance-tshirt",
        "description": "Lightweight moisture-wicking t-shirt with four-way stretch. Perfect for running, gym, or casual wear.",
        "category": "clothing", "price": 799, "stock": 50,
        "image_url": "/images/tshirt.jpg",
        "tags": ["clothing", "tshirt", "sports", "fitness", "black", "blue"],
        "metadata_extra": {"colors": ["black", "blue", "grey", "white"], "sizes": ["S", "M", "L", "XL"],
                           "cross_sell": ["prod_001", "prod_002"]},
    },
]

DEMO_POLICY = {
    "id": "pol_001",
    "merchant_id": "merchant_001",
    "max_purchase_amount": 50000,
    "max_discount_percentage": 20,
    "approval_required": True,
    "auto_refund_enabled": False,
    "allowed_actions": ["search", "recommend", "add_to_cart", "create_order", "get_payment_status"],
}


def seed_database():
    """Seed database with demo data if not already seeded."""
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Merchant).filter(Merchant.id == "merchant_001").first()
        if existing:
            return

        # Create merchant
        merchant = Merchant(**DEMO_MERCHANT)
        db.add(merchant)

        # Create products
        for prod_data in DEMO_PRODUCTS:
            product = Product(
                id=prod_data["id"],
                merchant_id="merchant_001",
                name=prod_data["name"],
                slug=prod_data["slug"],
                description=prod_data["description"],
                category=prod_data["category"],
                price=prod_data["price"],
                currency="INR",
                stock=prod_data["stock"],
                active=True,
                image_url=prod_data.get("image_url", ""),
                tags=prod_data.get("tags", []),
                metadata_extra=prod_data.get("metadata_extra", {}),
            )
            db.add(product)

        # Create policy
        policy = Policy(**DEMO_POLICY)
        db.add(policy)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
