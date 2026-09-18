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
        cart_id=cart.id,
        amount=62000,
        status="created",
        razorpay_order_id="order_test_payment_service_v2",
    )

    db.add(order)
    db.commit()

    order = update_payment_status(
        db=db,
        razorpay_order_id="order_test_payment_service_v2",
        status="paid",
    )

    print(
        order.id,
        order.razorpay_order_id,
        order.status,
    )

finally:
    db.close()