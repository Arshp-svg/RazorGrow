from sqlalchemy.orm import Session

from app.models.models import AuditLog, Order


def get_dashboard_metrics(db: Session):
    orders = db.query(Order).all()

    total_orders = len(orders)

    successful_payments = sum(
        1
        for order in orders
        if order.status == "paid"
    )

    failed_payments = sum(
        1
        for order in orders
        if order.status == "failed"
    )
    created_orders = sum(
    1
    for order in orders
    if order.status == "created"
)

    revenue = sum(
        order.amount
        for order in orders
        if order.status == "paid"
    )

    recovered_payments = sum(
        1
        for order in orders
        if order.status == "paid"
        and any(
            audit.entity_id == str(order.id)
            and audit.action == "payment_status_updated"
            and audit.external_result == "failed"
            for audit in db.query(AuditLog).all()
        )
    )
    
    recovered_revenue = sum(
    order.amount
    for order in orders
    if order.status == "paid"
    and any(
        audit.entity_id == str(order.id)
        and audit.action == "payment_status_updated"
        and audit.external_result == "failed"
        for audit in db.query(AuditLog).all()
    )
)

    policy_blocks = sum(
        1
        for audit in db.query(AuditLog).all()
        if audit.action == "policy_evaluated"
        and audit.policy_result == "BLOCKED"
    )

    average_order_value = (
        revenue / successful_payments
        if successful_payments > 0
        else 0
    )

    payment_conversion_rate = (
        (successful_payments / total_orders) * 100
        if total_orders > 0
        else 0
    )

    return {
        "total_orders": total_orders,
        "created_orders": created_orders,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "recovered_payments": recovered_payments,
        "revenue": revenue,
        "recovered_revenue": recovered_revenue,
        "average_order_value": round(
            average_order_value,
            2,
        ),
        "payment_conversion_rate": round(
            payment_conversion_rate,
            2,
        ),
        "policy_blocks": policy_blocks,
    }