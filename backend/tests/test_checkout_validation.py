from app.db.database import SessionLocal
from app.models.models import Cart
from app.services.cart_service import validate_checkout


db = SessionLocal()

try:
    cart = (
        db.query(Cart)
        .filter(Cart.id == 2)
        .first()
    )

    if cart is None:
        raise RuntimeError("Cart 2 not found")

    try:
        validate_checkout(cart)
        print("Checkout validation: PASS")
    except ValueError as exc:
        print("Checkout validation: FAIL")
        print("Reason:", exc)

finally:
    db.close()