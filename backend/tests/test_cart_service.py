from app.db.database import SessionLocal
from app.services.cart_service import (
    add_to_cart,
    get_or_create_cart,
)


db = SessionLocal()

try:
    cart = get_or_create_cart(
        db,
        customer_id="test-customer-day6",
    )

    cart = add_to_cart(
        db,
        cart,
        product_id=1,
        quantity=1,
    )

    print("Cart ID:", cart.id)
    print("Status:", cart.status)
    print("Items:")

    for item in cart.items:
        print(
            item.product_id,
            item.quantity,
            item.unit_price,
        )

    print("Subtotal:", cart.subtotal)
    print("Total:", cart.total)

finally:
    db.close()