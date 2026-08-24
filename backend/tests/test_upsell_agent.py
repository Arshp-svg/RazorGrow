from app.db.database import SessionLocal
from app.agents.upsell_agent import UpsellAgent
from app.services.upsell_service import recommend_upsell


db = SessionLocal()

try:
    result = recommend_upsell(
        db,
        product_id=1,
    )

    explanation = UpsellAgent().explain(result)

    print("Original:")
    print(
        result.original_product_name,
        result.original_value,
    )

    print("\nUpsell:")
    print(
        result.upsell.name,
        result.upsell.price,
        result.upsell.inventory,
        result.upsell.score,
    )

    print("\nExplanation:")
    print(explanation)

    print("\nAccepted:")
    print(result.accepted)

finally:
    db.close()