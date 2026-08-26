from app.db.database import SessionLocal
from app.services.checkout_service import create_checkout_order


db = SessionLocal()

try:
    result = create_checkout_order(
        db,
        cart_id=2,
        confirmed=True,
    )

    print(result)

finally:
    db.close()