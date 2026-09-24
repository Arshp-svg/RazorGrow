from datetime import datetime

from app.auth.roles import MerchantRole
from app.db.database import SessionLocal
from app.models.models import (
    AuditLog,
    Cart,
    CartItem,
    Merchant,
    MerchantMembership,
    Order,
    Policy,
    Product,
    User,
)
from app.services.auth_service import hash_password


DEMO_PASSWORD = "DemoPassword123!"


def seed_demo_data() -> None:
    db = SessionLocal()

    try:
        existing = (
            db.query(Merchant)
            .filter(Merchant.name == "RazorGrow Demo Merchant 1")
            .first()
        )

        if existing is not None:
            print("Demo data already exists; nothing to do.")
            return

        merchant_1 = Merchant(
            name="RazorGrow Demo Merchant 1",
            status="active",
            settings='{"seed":"day4-demo-1"}',
        )
        merchant_2 = Merchant(
            name="RazorGrow Demo Merchant 2",
            status="active",
            settings='{"seed":"day4-demo-2"}',
        )
        db.add_all([merchant_1, merchant_2])
        db.flush()

        user_1 = User(
            email="day4-owner@demo.razorgrow.local",
            password_hash=hash_password(DEMO_PASSWORD),
            is_active=True,
        )
        user_2 = User(
            email="day4-viewer@demo.razorgrow.local",
            password_hash=hash_password(DEMO_PASSWORD),
            is_active=True,
        )
        db.add_all([user_1, user_2])
        db.flush()

        db.add_all(
            [
                MerchantMembership(
                    merchant_id=merchant_1.id,
                    user_id=user_1.id,
                    role=MerchantRole.OWNER.value,
                ),
                MerchantMembership(
                    merchant_id=merchant_2.id,
                    user_id=user_2.id,
                    role=MerchantRole.VIEWER.value,
                ),
            ]
        )

        product_1 = Product(
            merchant_id=merchant_1.id,
            name="Demo Laptop",
            price=65000,
            category="laptop",
            tags="demo,portable",
            use_cases="programming,work",
            compatible_products="",
            upsell_products="",
            inventory=10,
        )
        product_2 = Product(
            merchant_id=merchant_2.id,
            name="Demo Monitor",
            price=25000,
            category="monitor",
            tags="demo,display",
            use_cases="work,gaming",
            compatible_products="",
            upsell_products="",
            inventory=8,
        )
        db.add_all([product_1, product_2])
        db.flush()

        cart_1 = Cart(
            merchant_id=merchant_1.id,
            customer_id="day4-demo-customer-1",
            status="active",
            subtotal=65000,
            total=65000,
        )
        cart_2 = Cart(
            merchant_id=merchant_2.id,
            customer_id="day4-demo-customer-2",
            status="active",
            subtotal=25000,
            total=25000,
        )
        db.add_all([cart_1, cart_2])
        db.flush()

        db.add_all(
            [
                CartItem(
                    cart_id=cart_1.id,
                    product_id=product_1.id,
                    quantity=1,
                    unit_price=65000,
                ),
                CartItem(
                    cart_id=cart_2.id,
                    product_id=product_2.id,
                    quantity=1,
                    unit_price=25000,
                ),
            ]
        )

        order_1 = Order(
            merchant_id=merchant_1.id,
            cart_id=cart_1.id,
            amount=65000,
            status="created",
            razorpay_order_id=None,
        )
        order_2 = Order(
            merchant_id=merchant_2.id,
            cart_id=cart_2.id,
            amount=25000,
            status="created",
            razorpay_order_id=None,
        )
        db.add_all([order_1, order_2])
        db.flush()

        db.add_all(
            [
                Policy(
                    merchant_id=merchant_1.id,
                    max_order_amount=100000,
                    max_discount=10,
                    confirmation_required=True,
                    approval_threshold=75000,
                ),
                Policy(
                    merchant_id=merchant_2.id,
                    max_order_amount=50000,
                    max_discount=5,
                    confirmation_required=True,
                    approval_threshold=40000,
                ),
            ]
        )

        timestamp = datetime(2026, 1, 1, 0, 0, 0)

        db.add_all(
            [
                AuditLog(
                    merchant_id=merchant_1.id,
                    timestamp=timestamp,
                    action="demo_seed_created",
                    entity_id=str(merchant_1.id),
                    policy_result="seeded",
                    external_result=None,
                    error=None,
                    recovery=None,
                ),
                AuditLog(
                    merchant_id=merchant_2.id,
                    timestamp=timestamp,
                    action="demo_seed_created",
                    entity_id=str(merchant_2.id),
                    policy_result="seeded",
                    external_result=None,
                    error=None,
                    recovery=None,
                ),
            ]
        )

        db.commit()

        print("Deterministic Day 4 demo data seeded successfully.")
        print(f"Merchant 1 ID: {merchant_1.id}")
        print(f"Merchant 2 ID: {merchant_2.id}")
        print(f"User 1 ID: {user_1.id}")
        print(f"User 2 ID: {user_2.id}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
