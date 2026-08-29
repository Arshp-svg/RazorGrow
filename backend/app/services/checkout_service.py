from sqlalchemy.orm import Session

from app.models.models import Cart, Order, Policy
from app.services.audit_service import record_audit
from app.services.cart_service import validate_checkout
from app.services.razorpay_service import (
    create_test_order,
    verify_order_amount,
)
from app.services.policy_service import evaluate_policy


def create_checkout_order(
    db: Session,
    cart_id: int,
    confirmed: bool,
):
    # if not confirmed:
    #     raise ValueError(
    #         "Checkout requires explicit customer confirmation"
    #     )

    cart = (
        db.query(Cart)
        .filter(Cart.id == cart_id)
        .first()
    )

    if cart is None:
        raise ValueError(
            f"Cart {cart_id} not found"
        )

    validate_checkout(cart)
    
    policy = (
        db.query(Policy)
        .order_by(Policy.id.desc())
        .first()
    )

    if policy is None:
        raise ValueError(
            "No merchant policy configured"
        )

    decision = evaluate_policy(
        policy=policy,
        order_amount=cart.total,
        discount=0,
        confirmed=confirmed,
    )
    
    record_audit(
    db=db,
    action="policy_evaluated",
    entity_id=str(cart.id),
    policy_result=decision.decision,
    external_result=None,
    error=None,
    recovery=None,
)

    if decision.decision != "APPROVED":
        raise ValueError(
            f"Policy blocked checkout: "
            f"{decision.reason}"
        )

    amount_in_paise = int(
        round(cart.total * 100)
    )
    
    

    razorpay_order = create_test_order(
        amount_in_paise
    )
    
    record_audit(
    db=db,
    action="razorpay_order_created",
    entity_id=str(cart.id),
    policy_result=decision.decision,
    external_result=razorpay_order["id"],
    error=None,
    recovery=None,
)
    
    amount_verified = verify_order_amount(
    cart_total=cart.total,
    razorpay_amount=razorpay_order["amount"],
)

    if not amount_verified:
        record_audit(
            db=db,
            action="payment_amount_verification",
            entity_id=str(cart.id),
            policy_result=decision.decision,
            external_result="amount_mismatch",
            error="Payment amount verification failed",
            recovery="checkout_blocked",
    )

        raise ValueError(
            "Payment amount verification failed"
        )

    record_audit(
        db=db,
        action="payment_amount_verification",
        entity_id=str(cart.id),
        policy_result=decision.decision,
        external_result="amount_verified",
        error=None,
        recovery=None,
    )
    
    local_order = Order(
        cart_id=cart.id,
        amount=cart.total,
        status=razorpay_order["status"],
        razorpay_order_id=razorpay_order["id"],
    )

    db.add(local_order)
    db.commit()
    db.refresh(local_order)

    return {
    "local_order_id": local_order.id,
    "cart_id": cart.id,
    "amount": cart.total,
    "amount_in_paise": amount_in_paise,
    "currency": razorpay_order["currency"],
    "razorpay_order_id": razorpay_order["id"],
    "status": local_order.status,
} 