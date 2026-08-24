from app.db.database import SessionLocal
from app.schemas.intent import ShoppingIntent
from app.services.recommendation_service import recommend_products


db = SessionLocal()

try:
    intent = ShoppingIntent(
        category="laptop",
        budget=70000,
        use_case="programming",
        constraints=["portable"],
    )

    result = recommend_products(db, intent)

    print("Intent:")
    print(result.intent)

    print("\nRecommendations:")

    for item in result.recommendations:
        print(
            item.product_id,
            item.name,
            item.price,
            item.inventory,
            item.score,
        )

finally:
    db.close()