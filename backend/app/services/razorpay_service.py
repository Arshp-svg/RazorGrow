import razorpay

from app.config import settings


client = razorpay.Client(
    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
)


def verify_connection() -> bool:
    try:
        response = client.payment.all({"count": 1})
        print("Razorpay response received.")
        print("Payment count:", response.get("count"))
        return True
    except Exception as e:
        print("Razorpay error:", repr(e))
        return False
    

def create_test_order(amount: int):
    return client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "receipt": "razorgrow_test_receipt",
        }
    )