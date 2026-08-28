from unittest.mock import patch

from app.db.database import SessionLocal
from app.models.models import Policy
from app.services.checkout_service import create_checkout_order


db = SessionLocal()

try:
    policy = Policy(
        max_order_amount=100000,
        max_discount=10,
        confirmation_required=True,
        approval_threshold=90000,
    )

    db.add(policy)
    db.commit()

    fake_razorpay_order = {
    "id": "order_day8_payment_test",
    "status": "created",
    "currency": "INR",
    "amount": 6200000,
}

    with patch(
        "app.services.checkout_service.create_test_order",
        return_value=fake_razorpay_order,
    ):
        result = create_checkout_order(
            db=db,
            cart_id=5 ,
            confirmed=True,
        )

    print(result)

finally:
    db.close()