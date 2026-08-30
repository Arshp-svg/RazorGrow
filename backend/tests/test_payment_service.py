from app.db.database import SessionLocal
from app.services.payment_service import update_payment_status


db = SessionLocal()

try:
    order = update_payment_status(
        db=db,
        razorpay_order_id="order_TVnOLxpIx9Swrc",
        status="paid"
    )

    print(
        order.id,
        order.razorpay_order_id,
        order.status,
    )

finally:
    db.close()