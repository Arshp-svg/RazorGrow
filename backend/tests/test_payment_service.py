from app.db.database import SessionLocal
from app.models.models import Cart, Order
from app.services.payment_service import update_payment_status


db = SessionLocal()

try:
    cart = Cart(
        customer_id="test_payment_customer",
        status="active",
        subtotal=62000,
        total=62000,
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    order = Order(
    merchant_id=1,
    cart_id=cart.id,
    idempotency_key="day7-payment-service-test-unique",
    amount=62000,
    status="created",
    razorpay_order_id="order_day7_payment_service_test",
)

    db.add(order)
    db.commit()

    order = update_payment_status(
        db=db,
        razorpay_order_id="order_day7_payment_service_test",
        status="paid",
    )

    print(
        order.id,
        order.razorpay_order_id,
        order.status,
    )

finally:
    db.close()