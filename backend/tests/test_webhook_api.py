import hashlib
import hmac
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db.database import SessionLocal
from app.main import app
from app.models.models import Cart, Order

client = TestClient(app)


def compute_sig(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


def create_order_for_api_test(db, status="created"):
    cart = Cart(
        merchant_id=1,
        customer_id=f"test-api-cust-{uuid.uuid4()}",
        status="active",
        subtotal=45000,
        total=45000,
    )
    db.add(cart)
    db.commit()
    db.refresh(cart)

    order = Order(
        merchant_id=1,
        cart_id=cart.id,
        idempotency_key=f"test-api-order-{uuid.uuid4()}",
        amount=45000,
        status=status,
        razorpay_order_id=f"order_api_{uuid.uuid4().hex[:12]}",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def test_webhook_endpoint_missing_signature():
    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured"}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert "Missing X-Razorpay-Signature header" in response.text


def test_webhook_endpoint_invalid_signature(monkeypatch):
    monkeypatch.setattr(settings, "razorpay_webhook_secret", "real_webhook_secret")
    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured"}',
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_sig",
        },
    )
    assert response.status_code == 400
    assert "Invalid webhook signature" in response.text


def test_webhook_endpoint_valid_event(monkeypatch):
    webhook_secret = "test_api_secret_xyz"
    monkeypatch.setattr(settings, "razorpay_webhook_secret", webhook_secret)

    db = SessionLocal()
    try:
        order = create_order_for_api_test(db, status="created")
        event_id = f"evt_api_{uuid.uuid4().hex}"

        payload_dict = {
            "entity": "event",
            "event": "payment.captured",
            "id": event_id,
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4().hex[:10]}",
                        "order_id": order.razorpay_order_id,
                        "status": "captured",
                        "amount": 4500000,
                    }
                }
            },
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        sig = compute_sig(payload_bytes, webhook_secret)

        response = client.post(
            "/webhooks/razorpay",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
                "X-Razorpay-Event-Id": event_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["data"]["status"] == "processed"
        assert data["data"]["order_status"] == "paid"

        db.refresh(order)
        assert order.status == "paid"

        # Test duplicate event handling through the API
        dup_response = client.post(
            "/webhooks/razorpay",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
                "X-Razorpay-Event-Id": event_id,
            },
        )
        assert dup_response.status_code == 200
        dup_data = dup_response.json()
        assert dup_data["status"] == "ok"
        assert dup_data["data"]["status"] == "already_processed"

    finally:
        db.close()
