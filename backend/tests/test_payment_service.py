import uuid

import pytest

from app.db.database import SessionLocal
from app.models.models import Cart, Order
from app.services.payment_service import update_payment_status


def create_test_order(db, status="created"):
    cart = Cart(
        customer_id=f"day7-payment-test-{uuid.uuid4()}",
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
        idempotency_key=f"day7-payment-test-{uuid.uuid4()}",
        amount=62000,
        status=status,
        razorpay_order_id=f"order_day7_payment_test_{uuid.uuid4()}",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def test_created_to_paid():
    db = SessionLocal()

    try:
        order = create_test_order(db, "created")

        updated = update_payment_status(
            db=db,
            razorpay_order_id=order.razorpay_order_id,
            status="paid",
        )

        assert updated.status == "paid"

    finally:
        db.close()


def test_created_to_failed_to_paid():
    db = SessionLocal()

    try:
        order = create_test_order(db, "created")

        failed = update_payment_status(
            db=db,
            razorpay_order_id=order.razorpay_order_id,
            status="failed",
        )
        assert failed.status == "failed"

        paid = update_payment_status(
            db=db,
            razorpay_order_id=order.razorpay_order_id,
            status="paid",
        )
        assert paid.status == "paid"

    finally:
        db.close()


@pytest.mark.parametrize(
    ("current_status", "next_status"),
    [
        ("created", "created"),
        ("failed", "failed"),
        ("paid", "failed"),
        ("paid", "paid"),
    ],
)
def test_invalid_payment_transitions(
    current_status,
    next_status,
):
    db = SessionLocal()

    try:
        order = create_test_order(
            db,
            current_status,
        )

        with pytest.raises(
            ValueError,
            match="Invalid payment state transition",
        ):
            update_payment_status(
                db=db,
                razorpay_order_id=order.razorpay_order_id,
                status=next_status,
            )

    finally:
        db.close()
