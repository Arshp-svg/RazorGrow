from unittest.mock import patch

from app.db.database import SessionLocal
from app.models.models import Cart, CartItem, Policy, Product
from app.services.checkout_service import create_checkout_order


db = SessionLocal()

try:
    product = Product(
        name="Test Laptop",
        price=62000,
        category="laptop",
        tags="test",
        use_cases="testing",
        compatible_products="",
        upsell_products="",
        inventory=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    cart = Cart(
        customer_id="test_customer",
        status="active",
        subtotal=62000,
        total=62000,
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    cart_item = CartItem(
        cart_id=cart.id,
        product_id=product.id,
        quantity=1,
        unit_price=62000,
    )

    db.add(cart_item)

    policy = Policy(
        max_order_amount=100000,
        max_discount=10,
        confirmation_required=True,
        approval_threshold=90000,
    )

    db.add(policy)
    db.commit()

    fake_razorpay_order = {
        "id": "order_test_checkout_service",
        "status": "created",
        "currency": "INR",
        "amount": 6200000,
    }

    with patch(
        "app.services.checkout_service.create_test_order",
        return_value=fake_razorpay_order,
    ):
        result = create_checkout_order(
            db=db,
            cart_id=cart.id,
            confirmed=True,
        )

    print(result)

finally:
    db.close()