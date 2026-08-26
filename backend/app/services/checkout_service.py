from sqlalchemy.orm import Session

from app.models.models import Cart, Policy

from app.services.cart_service import validate_checkout
from app.services.razorpay_service import create_test_order
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

    return {
        "cart_id": cart.id,
        "amount": cart.total,
        "amount_in_paise": amount_in_paise,
        "currency": razorpay_order["currency"],
        "razorpay_order_id": razorpay_order["id"],
        "status": razorpay_order["status"],
    } 