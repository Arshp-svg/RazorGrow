import uuid
from unittest.mock import patch

from app.db.database import SessionLocal
from app.models.models import Cart, CartItem, Merchant, Policy, Product
from app.services.checkout_service import create_checkout_order


def test_checkout_order_idempotency():
    db = SessionLocal()

    try:
        merchant = (
            db.query(Merchant)
            .filter(Merchant.name == "Day 7 Checkout Test Merchant")
            .first()
        )

        if merchant is None:
            merchant = Merchant(
                name="Day 7 Checkout Test Merchant",
                status="active",
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)

        product = Product(
            name="Test Laptop",
            price=62000,
            category="laptop",
            tags="test",
            use_cases="testing",
            compatible_products="",
            upsell_products="",
            inventory=10,
            merchant_id=merchant.id,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        cart = Cart(
            customer_id="test_customer",
            status="active",
            merchant_id=merchant.id,
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
            merchant_id=merchant.id,
        )

        db.add(policy)
        db.commit()

        fake_razorpay_order = {
            "id": "order_test_checkout_service",
            "status": "created",
            "currency": "INR",
            "amount": 6200000,
        }

        idempotency_key = f"day7-checkout-service-test-{uuid.uuid4()}"

        with patch(
            "app.services.checkout_service.create_test_order",
            return_value=fake_razorpay_order,
        ) as mock_create_test_order:
            result = create_checkout_order(
                db=db,
                cart_id=cart.id,
                confirmed=True,
                merchant_id=merchant.id,
                idempotency_key=idempotency_key,
            )

            retry_result = create_checkout_order(
                db=db,
                cart_id=cart.id,
                confirmed=True,
                merchant_id=merchant.id,
                idempotency_key=idempotency_key,
            )

        assert retry_result["local_order_id"] == result["local_order_id"]
        assert retry_result["razorpay_order_id"] == result["razorpay_order_id"]
        assert mock_create_test_order.call_count == 1

    finally:
        db.close()