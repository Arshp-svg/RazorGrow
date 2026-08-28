from sqlalchemy.orm import Session

from app.models.models import Order


def update_payment_status(
    db: Session,
    razorpay_order_id: str,
    status: str,
):
    allowed_statuses = {
        "paid",
        "failed",
    }

    if status not in allowed_statuses:
        raise ValueError(
            f"Invalid payment status: {status}"
        )

    order = (
        db.query(Order)
        .filter(
            Order.razorpay_order_id
            == razorpay_order_id
        )
        .first()
    )

    if order is None:
        raise ValueError(
            "Order not found"
        )

    order.status = status

    db.commit()
    db.refresh(order)

    return order