from app.db.database import SessionLocal
from app.services.upsell_service import recommend_upsell


db = SessionLocal()

try:
    result = recommend_upsell(
        db,
        product_id=1,
    )

    print("Original:")
    print(
        result.original_product_name,
        result.original_value,
    )

    print("\nUpsell:")

    if result.upsell:
        print(
            result.upsell.product_id,
            result.upsell.name,
            result.upsell.price,
            result.upsell.inventory,
            result.upsell.score,
        )
    else:
        print("No upsell")

    print("\nUpsell value:")
    print(result.upsell_value)

    print("\nAccepted:")
    print(result.accepted)

finally:
    db.close()