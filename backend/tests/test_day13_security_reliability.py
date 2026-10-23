import json
import uuid
import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.models.models import (
    ApprovalRequest,
    Cart,
    CartItem,
    Merchant,
    MerchantMembership,
    Order,
    Product,
    User,
)
from app.security.rate_limiter import auth_limiter
from app.services.auth_service import create_access_token, hash_password
from app.services.cart_service import add_to_cart, get_or_create_cart
from app.services.trace_service import get_execution_trace, start_execution

client = TestClient(app)


def create_user_for_tenant(db, merchant_id: int, role: str = "OWNER") -> tuple[User, str]:
    user = User(
        email=f"sec_test_{uuid.uuid4().hex[:8]}@merchant{merchant_id}.com",
        password_hash=hash_password("SuperSecure_123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    membership = MerchantMembership(
        merchant_id=merchant_id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    db.commit()

    token = create_access_token(user_id=user.id)
    return user, token


def test_security_headers_present():
    """Verify production security headers on API responses."""
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_rate_limiting_enforcement_and_recovery():
    """Verify rate limiter blocks bursts on sensitive auth endpoints with 429 and Retry-After."""
    auth_limiter.reset()

    # auth_limiter has max_requests = 10 per 60s
    try:
        status_codes = []
        for _ in range(12):
            resp = client.post(
                "/auth/login",
                json={"email": "nonexistent@example.com", "password": "wrongpassword"},
            )
            status_codes.append(resp.status_code)

        # First 10 should be 401 (invalid credentials)
        assert status_codes[:10] == [401] * 10
        # 11th and 12th should be 429 Too Many Requests
        assert status_codes[10] == 429
        assert status_codes[11] == 429
    finally:
        auth_limiter.reset()


def test_consistent_validation_error_envelope():
    """Verify FastAPI RequestValidationError returns standard error envelope."""
    # Send invalid type for budget_limit (string instead of float)
    response = client.post(
        "/ai/buyer/procure",
        json={"merchant_id": 1, "query": "Test", "budget_limit": "not_a_valid_number"},
    )
    assert response.status_code == 422
    data = response.json()

    assert data["error"] == "validation_error"
    assert "Invalid request parameters" in data["message"]
    assert "validation_errors" in data
    assert data["status_code"] == 422


def test_tenant_isolation_cross_tenant_rejection():
    """Verify strict tenant isolation: Tenant 2 cannot access or mutate Tenant 1 resources."""
    db = SessionLocal()
    try:
        # Ensure Merchant 2 exists
        m2 = db.query(Merchant).filter(Merchant.id == 2).first()
        if not m2:
            m2 = Merchant(id=2, name="Tenant 2 Store", status="active")
            db.add(m2)
            db.commit()

        # Create Tenant 1 user and Tenant 2 user
        _, token_tenant1 = create_user_for_tenant(db, merchant_id=1, role="OWNER")
        _, token_tenant2 = create_user_for_tenant(db, merchant_id=2, role="OWNER")

        headers_t1 = {"Authorization": f"Bearer {token_tenant1}"}
        headers_t2 = {"Authorization": f"Bearer {token_tenant2}"}

        # 1. Product Isolation: Tenant 2 cannot query Tenant 1's products via authenticated endpoint
        # Product 1 belongs to Merchant 1
        resp = client.get("/products/1", headers=headers_t2)
        assert resp.status_code == 404

        # 2. Cart Isolation: Create cart for Tenant 1
        cart_t1 = Cart(merchant_id=1, customer_id="cust_t1", status="active", subtotal=1000, total=1000)
        db.add(cart_t1)
        db.commit()
        db.refresh(cart_t1)

        # Tenant 2 attempts to confirm Tenant 1's cart
        resp = client.post(
            f"/checkout/{cart_t1.id}/confirm",
            headers=headers_t2,
            json={"confirmed": True, "idempotency_key": "sec_test_idemp_key"},
        )
        assert resp.status_code == 404

        # 3. Trace Isolation: Tenant 1 execution trace cannot be read by Tenant 2
        exec_t1 = start_execution(db, merchant_id=1, session_id="sec_t1_sess", intent="T1 query")
        trace_t2 = get_execution_trace(db, execution_id=exec_t1.id, merchant_id=2)
        assert trace_t2 is None

        # API call with Tenant 2 token
        resp = client.get(f"/agent/executions/{exec_t1.id}/trace", headers=headers_t2)
        assert resp.status_code == 404

    finally:
        db.close()


def test_password_hash_integrity():
    """Verify plaintext passwords are never stored in the database."""
    db = SessionLocal()
    try:
        raw_password = "SecretPassword123!"
        user, _ = create_user_for_tenant(db, merchant_id=1)

        db_user = db.query(User).filter(User.id == user.id).first()
        assert db_user is not None
        assert db_user.password_hash != raw_password
        assert len(db_user.password_hash) > 20
        # Verify hash begins with argon2 or pbkdf2 algorithm identifier
        assert db_user.password_hash.startswith("$argon2") or db_user.password_hash.startswith("$pbkdf2")
    finally:
        db.close()


def test_input_validation_negative_and_zero_quantity():
    """Verify negative or zero quantities are deterministically rejected."""
    db = SessionLocal()
    try:
        cart = Cart(merchant_id=1, customer_id="qty_test_cust", status="active", subtotal=0, total=0)
        db.add(cart)
        db.commit()
        db.refresh(cart)

        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            add_to_cart(db, cart, product_id=1, quantity=0)

        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            add_to_cart(db, cart, product_id=1, quantity=-5)
    finally:
        db.close()


def test_input_validation_insufficient_inventory():
    """Verify ordering more than available inventory is blocked."""
    db = SessionLocal()
    try:
        cart = Cart(merchant_id=1, customer_id="inv_test_cust", status="active", subtotal=0, total=0)
        db.add(cart)
        db.commit()
        db.refresh(cart)

        # ProBook 14 Laptop has inventory 12; attempting to add 100 units must fail
        with pytest.raises(ValueError, match="Insufficient inventory"):
            add_to_cart(db, cart, product_id=1, quantity=100)
    finally:
        db.close()
