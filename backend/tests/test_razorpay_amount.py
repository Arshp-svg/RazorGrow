from app.services.razorpay_service import verify_order_amount


print(
    "Correct amount:",
    verify_order_amount(
        cart_total=62000,
        razorpay_amount=6200000,
    ),
)

print(
    "Wrong amount:",
    verify_order_amount(
        cart_total=62000,
        razorpay_amount=5000000,
    ),
)