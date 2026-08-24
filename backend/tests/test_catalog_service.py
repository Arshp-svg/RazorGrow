from app.db.database import SessionLocal
from app.schemas.intent import ShoppingIntent
from app.services.catalog_service import (
    find_candidates,
    rank_candidates,
    score_product,
)


db = SessionLocal()

try:
    intent = ShoppingIntent(
        category="laptop",
        budget=70000,
        use_case="programming",
        constraints=["portable"],
    )

    candidates = find_candidates(db, intent)
    ranked_candidates = rank_candidates(candidates, intent)

    print("Candidate count:", len(candidates))

    for product in ranked_candidates:
        print(
            product.id,
            product.name,
            product.price,
            product.inventory,
            "score=",
            score_product(product, intent),
        )

finally:
    db.close()