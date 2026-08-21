from app.db.database import SessionLocal
from app.models.models import Product


products = [
    Product(name="ProBook 14 Laptop", price=62000),
    Product(name="CodeMaster 15 Laptop", price=68000),
    Product(name="UltraBook Air 13", price=59000),
    Product(name="Ergo Wireless Mouse", price=1200),
    Product(name="Mechanical Programming Keyboard", price=4500),
    Product(name="USB-C Laptop Hub", price=2200),
    Product(name="27-inch 4K Monitor", price=28000),
    Product(name="Laptop Cooling Pad", price=1800),
    Product(name="Noise Cancelling Headphones", price=8500),
    Product(name="Laptop Backpack", price=2500),
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