from unittest.mock import patch

from app.db.database import SessionLocal
from app.services.checkout_service import create_checkout_order


db = SessionLocal()

try:
    with patch(
        "app.services.checkout_service.create_test_order"
    ) as mock_create_order:

        # Intentionally return the WRONG Razorpay amount.
        mock_create_order.return_value = {
            "id": "order_day11_mismatch_test",
            "amount": 6100000,  # ₹61,000 instead of ₹62,000
            "currency": "INR",
            "status": "created",
        }

        try:
            result = create_checkout_order(
                db,
                cart_id=5,
                confirmed=True,
            )

            print("UNEXPECTED SUCCESS:")
            print(result)

        except ValueError as e:
            print("EXPECTED ERROR:")
            print(e)

finally:
    db.close()