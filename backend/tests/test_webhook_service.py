import hashlib
import hmac
import json
import uuid

import pytest

from app.db.database import SessionLocal
from app.models.models import Cart, Order, WebhookEvent
from app.services.webhook_service import (
    compute_payload_hash,
    process_webhook_payload,
    verify_webhook_signature,
)

TEST_WEBHOOK_SECRET = "test_webhook_secret_key_123"


def generate_signature(payload_bytes: bytes, secret: str = TEST_WEBHOOK_SECRET) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


def create_test_order(db, status="created"):
    cart = Cart(
        merchant_id=1,
        customer_id=f"test-webhook-cust-{uuid.uuid4()}",
        status="active",
        subtotal=70000,
        total=70000,
    )
    db.add(cart)
    db.commit()
    db.refresh(cart)

    order = Order(
        merchant_id=1,
        cart_id=cart.id,
        idempotency_key=f"test-webhook-order-{uuid.uuid4()}",
        amount=70000,
        status=status,
        razorpay_order_id=f"order_webhook_{uuid.uuid4().hex[:12]}",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def test_signature_verification_success():
    payload = b'{"event":"payment.captured"}'
    sig = generate_signature(payload)
    assert verify_webhook_signature(payload, sig, secret=TEST_WEBHOOK_SECRET) is True


def test_signature_verification_failure():
    payload = b'{"event":"payment.captured"}'
    assert verify_webhook_signature(payload, "invalid_signature", secret=TEST_WEBHOOK_SECRET) is False
    assert verify_webhook_signature(payload, None, secret=TEST_WEBHOOK_SECRET) is False
    assert verify_webhook_signature(payload, "", secret=TEST_WEBHOOK_SECRET) is False


def test_webhook_updates_order_to_paid():
    db = SessionLocal()
    try:
        order = create_test_order(db, status="created")
        event_id = f"evt_{uuid.uuid4().hex}"

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
                        "amount": 7000000,
                    }
                }
            },
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        sig = generate_signature(payload_bytes)

        result = process_webhook_payload(
            db=db,
            payload_bytes=payload_bytes,
            signature=sig,
            secret=TEST_WEBHOOK_SECRET,
        )

        assert result["status"] == "processed"
        assert result["provider_event_id"] == event_id
        assert result["order_status"] == "paid"

        db.refresh(order)
        assert order.status == "paid"

        # Check webhook event persisted
        saved_event = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.provider_event_id == event_id)
            .first()
        )
        assert saved_event is not None
        assert saved_event.processed is True
    finally:
        db.close()


def test_webhook_idempotency_prevents_duplicate_processing():
    db = SessionLocal()
    try:
        order = create_test_order(db, status="created")
        event_id = f"evt_{uuid.uuid4().hex}"

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
                    }
                }
            },
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        sig = generate_signature(payload_bytes)

        # First delivery
        first_result = process_webhook_payload(
            db=db,
            payload_bytes=payload_bytes,
            signature=sig,
            secret=TEST_WEBHOOK_SECRET,
        )
        assert first_result["status"] == "processed"

        # Second delivery (replay with same event id)
        second_result = process_webhook_payload(
            db=db,
            payload_bytes=payload_bytes,
            signature=sig,
            secret=TEST_WEBHOOK_SECRET,
        )
        assert second_result["status"] == "already_processed"
        assert second_result["provider_event_id"] == event_id
    finally:
        db.close()


def test_webhook_handles_payment_failure_event():
    db = SessionLocal()
    try:
        order = create_test_order(db, status="created")
        event_id = f"evt_{uuid.uuid4().hex}"

        payload_dict = {
            "entity": "event",
            "event": "payment.failed",
            "id": event_id,
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4().hex[:10]}",
                        "order_id": order.razorpay_order_id,
                        "status": "failed",
                    }
                }
            },
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        sig = generate_signature(payload_bytes)

        result = process_webhook_payload(
            db=db,
            payload_bytes=payload_bytes,
            signature=sig,
            secret=TEST_WEBHOOK_SECRET,
        )

        assert result["status"] == "processed"
        assert result["order_status"] == "failed"

        db.refresh(order)
        assert order.status == "failed"
    finally:
        db.close()


def test_webhook_rejects_invalid_signature():
    db = SessionLocal()
    try:
        payload_bytes = b'{"event":"payment.captured"}'
        with pytest.raises(ValueError, match="Invalid webhook signature"):
            process_webhook_payload(
                db=db,
                payload_bytes=payload_bytes,
                signature="bogus_signature",
                secret=TEST_WEBHOOK_SECRET,
            )
    finally:
        db.close()
