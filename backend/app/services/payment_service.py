from sqlalchemy.orm import Session
from app.services.audit_service import record_audit
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

    if order.status == "paid":
        raise ValueError(
            "Order is already paid"
        )

    order.status = status

    record_audit(
        db=db,
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

    db.refresh(order)

    return order