from app.db.database import SessionLocal
from app.models.models import Product
from app.services.upsell_service import (
    find_upsell_candidates,
    rank_upsell_candidates,
    score_upsell,
)

db = SessionLocal()

try:
    product = (
        db.query(Product)
        .filter(Product.name == "ProBook 14 Laptop")
        .first()
    )

    if product is None:
        raise RuntimeError("ProBook 14 Laptop not found")

    candidates = find_upsell_candidates(
        db,
        product,
    )
    
    ranked_candidates = rank_upsell_candidates(
    product,
    candidates,
)

    print("Base product:")
    print(product.name)

    print("\nUpsell candidates:")

    for candidate in ranked_candidates:
        print(
            candidate.id,
            candidate.name,
            candidate.price,
            candidate.inventory,
            "score=",
            score_upsell(product, candidate),
        )

finally:
    db.close()