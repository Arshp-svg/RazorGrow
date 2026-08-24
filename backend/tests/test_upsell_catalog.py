from app.db.database import SessionLocal
from app.models.models import Product


db = SessionLocal()

try:
    products = db.query(Product).all()

    print("Product relationships:")

    for product in products:
        print(
            f"\n{product.id}. {product.name}"
        )
        print(
            "  compatible_products:",
            product.compatible_products,
        )
        print(
            "  upsell_products:",
            product.upsell_products,
        )

finally:
    db.close()