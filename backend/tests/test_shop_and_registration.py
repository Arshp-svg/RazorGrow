import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.models import Order, Product

client = TestClient(app)


def test_merchant_self_serve_registration_and_shop_flow():
    email = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    shop_name = "Arsh's High-Tech Gear"

    # 1. Self-serve Register
    reg_resp = client.post(
        "/auth/register",
        json={"email": email, "password": password, "shop_name": shop_name},
    )
    assert reg_resp.status_code == 200, reg_resp.text
    user_data = reg_resp.json()
    assert user_data["email"] == email
    assert user_data["merchant_id"] is not None
    assert user_data["merchant_name"] == shop_name
    merchant_id = user_data["merchant_id"]

    # 2. Login
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None

    # 3. Add a Product to this Merchant's Catalog
    headers = {"Authorization": f"Bearer {token}"}
    create_prod_resp = client.post(
        "/products",
        json={
            "name": "Custom Gaming Laptop",
            "price": 65000.0,
            "category": "laptop",
            "tags": ["gaming", "performance"],
            "use_cases": ["gaming", "coding"],
            "inventory": 5,
        },
        headers=headers,
    )
    assert create_prod_resp.status_code == 200, create_prod_resp.text
    prod_data = create_prod_resp.json()
    assert prod_data["name"] == "Custom Gaming Laptop"
    assert prod_data["price"] == 65000.0
    product_id = prod_data["id"]

    # 4. Public Customer Visits Storefront: GET /shop/{merchant_id}/info
    shop_info_resp = client.get(f"/shop/{merchant_id}/info")
    assert shop_info_resp.status_code == 200
    shop_info = shop_info_resp.json()
    assert shop_info["store_name"] == shop_name
    assert shop_info["merchant_id"] == merchant_id
    assert len(shop_info["products"]) >= 1
    assert any(p["id"] == product_id for p in shop_info["products"])

    # 5. Public Customer Chats with the AI Sales Agent: POST /shop/{merchant_id}/chat
    chat_resp = client.post(
        f"/shop/{merchant_id}/chat",
        json={"message": "I need a gaming laptop for coding"},
    )
    assert chat_resp.status_code == 200, chat_resp.text
    chat_data = chat_resp.json()
    assert "reply" in chat_data
    assert chat_data["recommended_product"] is not None
    assert chat_data["recommended_product"]["id"] == product_id

    # 6. Public Customer Checks Out: POST /shop/{merchant_id}/checkout
    checkout_resp = client.post(
        f"/shop/{merchant_id}/checkout",
        json={
            "items": [{"product_id": product_id, "quantity": 1}],
            "customer_email": "buyer@example.com",
            "customer_name": "Test Gamer",
            "confirmed": True,
        },
    )
    assert checkout_resp.status_code == 200, checkout_resp.text
    checkout_data = checkout_resp.json()
    assert checkout_data["status"] == "SUCCESS"
    assert checkout_data["amount"] == 65000.0
    assert checkout_data["razorpay_order_id"] is not None
    order_id = checkout_data["order_id"]

    # 7. Customer Completes Payment: POST /shop/{merchant_id}/verify-payment
    verify_resp = client.post(
        f"/shop/{merchant_id}/verify-payment",
        json={
            "order_id": order_id,
            "razorpay_order_id": checkout_data["razorpay_order_id"],
            "razorpay_payment_id": f"pay_test_{uuid.uuid4().hex[:10]}",
        },
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == "paid"

    # Verify inventory was decremented in DB from 5 to 4
    db = SessionLocal()
    try:
        updated_prod = db.query(Product).filter(Product.id == product_id).first()
        assert updated_prod.inventory == 4
        updated_order = db.query(Order).filter(Order.id == order_id).first()
        assert updated_order.status == "paid"
    finally:
        db.close()


def test_merchant_shop_checkout_approval_threshold_trigger():
    # Test high-value order (> 90k threshold) triggers NEEDS_APPROVAL
    db = SessionLocal()
    try:
        email = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = client.post(
            "/auth/register",
            json={"email": email, "password": "SecurePassword123!", "shop_name": "Enterprise Workstations"},
        )
        assert reg_resp.status_code == 200
        merchant_id = reg_resp.json()["merchant_id"]

        # Add a 95k product
        prod = Product(
            merchant_id=merchant_id,
            name="Ultra Heavy Workstation",
            price=95000.0,
            category="workstation",
            tags="enterprise",
            use_cases="datacenter",
            inventory=2,
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id
    finally:
        db.close()

    # Customer attempts to checkout a 95,000 item
    checkout_resp = client.post(
        f"/shop/{merchant_id}/checkout",
        json={
            "items": [{"product_id": prod_id, "quantity": 1}],
            "customer_email": "cto@enterprise.com",
            "confirmed": True,
        },
    )
    assert checkout_resp.status_code == 200
    checkout_data = checkout_resp.json()
    assert checkout_data["status"] == "NEEDS_APPROVAL"
    assert "approval" in checkout_data["message"].lower()
