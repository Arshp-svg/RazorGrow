from app.db.database import SessionLocal
from app.models.models import Product


products = [
    Product(
        name="ProBook 14 Laptop",
        price=62000,
        category="laptop",
        tags="programming,portable,developer",
        use_cases="programming,software development,office work",
        compatible_products="4,5,6",
        upsell_products="7,9",
        inventory=12,
    ),
    Product(
        name="CodeMaster 15 Laptop",
        price=68000,
        category="laptop",
        tags="programming,performance,developer",
        use_cases="programming,software development,video editing",
        compatible_products="4,5,6",
        upsell_products="7,9",
        inventory=8,
    ),
    Product(
        name="UltraBook Air 13",
        price=59000,
        category="laptop",
        tags="lightweight,portable,student",
        use_cases="programming,office work,study",
        compatible_products="4,6,10",
        upsell_products="4,10",
        inventory=15,
    ),
    Product(
        name="Ergo Wireless Mouse",
        price=1200,
        category="mouse",
        tags="wireless,ergonomic,productivity",
        use_cases="programming,office work,productivity",
        compatible_products="1,2,3",
        upsell_products="",
        inventory=40,
    ),
    Product(
        name="Mechanical Programming Keyboard",
        price=4500,
        category="keyboard",
        tags="mechanical,programming,productivity",
        use_cases="programming,gaming,office work",
        compatible_products="1,2,3",
        upsell_products="4",
        inventory=25,
    ),
    Product(
        name="USB-C Laptop Hub",
        price=2200,
        category="accessory",
        tags="usb-c,connectivity,portable",
        use_cases="programming,office work,productivity",
        compatible_products="1,2,3",
        upsell_products="7",
        inventory=30,
    ),
    Product(
        name="27-inch 4K Monitor",
        price=28000,
        category="monitor",
        tags="4k,large-screen,productivity",
        use_cases="programming,design,video editing",
        compatible_products="1,2",
        upsell_products="5",
        inventory=10,
    ),
    Product(
        name="Laptop Cooling Pad",
        price=1800,
        category="accessory",
        tags="cooling,portable,laptop",
        use_cases="programming,gaming,heavy workloads",
        compatible_products="1,2,3",
        upsell_products="",
        inventory=20,
    ),
    Product(
        name="Noise Cancelling Headphones",
        price=8500,
        category="audio",
        tags="wireless,noise-cancelling,focus",
        use_cases="programming,office work,travel",
        compatible_products="1,2,3",
        upsell_products="",
        inventory=18,
    ),
    Product(
        name="Laptop Backpack",
        price=2500,
        category="accessory",
        tags="portable,travel,storage",
        use_cases="travel,study,office work",
        compatible_products="1,2,3",
        upsell_products="",
        inventory=22,
    ),
]


def seed_products():
    db = SessionLocal()

    try:
        existing_count = db.query(Product).count()

        if existing_count > 0:
            print(f"Products already exist: {existing_count}")
            return

        db.add_all(products)
        db.commit()

        print(f"Seeded {len(products)} products.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()