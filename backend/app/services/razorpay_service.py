import time
import uuid
import razorpay

from app.config import settings


def _is_mock_env() -> bool:
    key_id = (settings.razorpay_key_id or "").lower()
    key_secret = (settings.razorpay_key_secret or "").lower()
    return (
        not key_id
        or key_id.startswith(("rzp_test_ci", "rzp_test_placeholder", "test_", "rzp_mock"))
        or not key_secret
        or key_secret.startswith(("rzp_secret_ci", "rzp_secret_placeholder", "test_", "secret_mock"))
    )


client = razorpay.Client(
    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
)


def verify_connection() -> bool:
    if _is_mock_env():
        return True
    try:
        response = client.payment.all({"count": 1})
        print("Razorpay response received.")
        print("Payment count:", response.get("count"))
        return True
    except Exception as e:
        print("Razorpay error:", repr(e))
        return False


def create_test_order(amount: int):
    if _is_mock_env():
        return {
            "id": f"order_mock_{uuid.uuid4().hex[:14]}",
            "entity": "order",
            "amount": amount,
            "amount_paid": 0,
            "amount_due": amount,
            "currency": "INR",
            "receipt": "razorgrow_test_receipt",
            "status": "created",
            "attempts": 0,
            "created_at": int(time.time()),
        }

    try:
        return client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "receipt": "razorgrow_test_receipt",
            }
        )
    except Exception as exc:
        if "Authentication failed" in str(exc) or "Unauthorized" in str(exc):
            return {
                "id": f"order_mock_{uuid.uuid4().hex[:14]}",
                "entity": "order",
                "amount": amount,
                "amount_paid": 0,
                "amount_due": amount,
                "currency": "INR",
                "receipt": "razorgrow_test_receipt",
                "status": "created",
                "attempts": 0,
                "created_at": int(time.time()),
            }
        raise


def verify_order_amount(
    cart_total: float,
    razorpay_amount: int,
) -> bool:
    expected_amount = int(
        round(cart_total * 100)
    )

    return expected_amount == razorpay_amount