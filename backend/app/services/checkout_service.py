from sqlalchemy.orm import Session

from app.models.models import Cart
from app.services.cart_service import validate_checkout
from app.services.razorpay_service import create_test_order


def create_checkout_order(
    db: Session,
    cart_id: int,
    confirmed: bool,
):
    if not confirmed:
        raise ValueError(
            "Checkout requires explicit customer confirmation"
        )

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