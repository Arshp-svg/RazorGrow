from sqlalchemy.orm import Session

from app.models.models import Order
from app.services.audit_service import record_audit


PAYMENT_TRANSITIONS = {
    "created": {"paid", "failed"},
    "failed": {"paid"},
    "paid": set(),
}


def update_payment_status(
    db: Session,
    razorpay_order_id: str,
    status: str,
):
    if status not in PAYMENT_TRANSITIONS:
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

    allowed_next_states = PAYMENT_TRANSITIONS.get(
        order.status,
        set(),
    )

    if status not in allowed_next_states:
        raise ValueError(
            f"Invalid payment state transition: "
            f"{order.status} -> {status}"
        )

    order.status = status

    record_audit(
        db=db,
        merchant_id=order.merchant_id,
        action="payment_status_updated",
        entity_id=str(order.id),
        policy_result=None,
        external_result=status,
        error=None,
        recovery=(
            "retry_available"
            if status == "failed"
            else None
        ),
    )

    db.commit()
    db.refresh(order)

    return order
