import json
import uuid

import pytest

from app.db.database import SessionLocal
from app.models.models import AuditLog, Cart, Order
from app.services.failure_service import (
    MAX_PAYMENT_RETRIES,
    FailureCategory,
    can_retry_payment,
    classify_failure,
    execute_payment_retry,
    get_order_retry_count,
)
from app.services.webhook_service import process_webhook_payload


def test_classify_failure_categories():
    # Retryable
    c1 = classify_failure("GATEWAY_TIMEOUT")
    assert c1.category == FailureCategory.RETRYABLE
    assert c1.is_retryable is True

    c2 = classify_failure(None, http_status=503)
    assert c2.category == FailureCategory.RETRYABLE

    # Customer action required
    c3 = classify_failure("PAYMENT_DECLINED")
    assert c3.category == FailureCategory.CUSTOMER_ACTION_REQUIRED
    assert c3.is_retryable is True

    c4 = classify_failure("INSUFFICIENT_FUNDS")
    assert c4.category == FailureCategory.CUSTOMER_ACTION_REQUIRED

    # Invalid request
    c5 = classify_failure("AMOUNT_MISMATCH")
    assert c5.category == FailureCategory.INVALID_REQUEST
    assert c5.is_retryable is False

    # Policy blocked
    c6 = classify_failure("LIMIT_EXCEEDED")
    assert c6.category == FailureCategory.POLICY_BLOCKED
    assert c6.is_retryable is False


def create_order(db, status="failed"):
    cart = Cart(
        merchant_id=1,
        customer_id=f"test-cust-{uuid.uuid4()}",
        status="active",
        subtotal=50000,
        total=50000,
    )
    db.add(cart)
    db.commit()
    db.refresh(cart)

    order = Order(
        merchant_id=1,
        cart_id=cart.id,
        idempotency_key=f"test-order-key-{uuid.uuid4()}",
        amount=50000,
        status=status,
        razorpay_order_id=f"order_fail_test_{uuid.uuid4().hex[:12]}",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def test_can_retry_payment_validates_status():
    db = SessionLocal()
    try:
        # Order already paid cannot be retried
        paid_order = create_order(db, status="paid")
        allowed, msg, _ = can_retry_payment(db, paid_order)
        assert allowed is False
        assert "already paid" in msg

        # Order still created cannot be retried
        created_order = create_order(db, status="created")
        allowed, msg, _ = can_retry_payment(db, created_order)
        assert allowed is False
        assert "only allowed from" in msg

        # Order failed can be retried
        failed_order = create_order(db, status="failed")
        allowed, msg, count = can_retry_payment(db, failed_order)
        assert allowed is True
        assert count == 0
    finally:
        db.close()


def test_execute_payment_retry_recovers_to_paid():
    db = SessionLocal()
    try:
        order = create_order(db, status="failed")
        initial_order_id = order.id
        initial_razorpay_id = order.razorpay_order_id

        # Retry and recover to paid
        result = execute_payment_retry(db, order=order, target_status="paid")

        assert result["status"] == "paid"
        assert result["order_id"] == initial_order_id
        assert result["retry_count"] == 1
        assert result["recovery"] == "recovered"

        # Verify no duplicate order was created
        db.refresh(order)
        assert order.status == "paid"
        assert order.razorpay_order_id == initial_razorpay_id

        # Verify audit entry for retry
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(order.id),
                AuditLog.action == "payment_retry_attempted",
            )
            .first()
        )
        assert audit is not None
        assert "attempt_1" in audit.external_result
    finally:
        db.close()


def test_bounded_retry_enforces_limit():
    db = SessionLocal()
    try:
        order = create_order(db, status="failed")

        # Perform retries up to limit (3 attempts)
        for i in range(MAX_PAYMENT_RETRIES):
            res = execute_payment_retry(
                db,
                order=order,
                target_status="failed",
                error_code="PAYMENT_DECLINED",
                max_retries=MAX_PAYMENT_RETRIES,
            )
            assert res["status"] == "failed"
            assert res["retry_count"] == i + 1

        # Attempt 4 should be blocked
        allowed, reason, count = can_retry_payment(
            db, order, max_retries=MAX_PAYMENT_RETRIES
        )
        assert allowed is False
        assert count == MAX_PAYMENT_RETRIES
        assert "exceeded" in reason

        with pytest.raises(ValueError, match="exceeded"):
            execute_payment_retry(
                db, order, target_status="paid", max_retries=MAX_PAYMENT_RETRIES
            )

        # Verify audit blocked event
        blocked_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(order.id),
                AuditLog.action == "payment_retry_blocked",
            )
            .first()
        )
        assert blocked_audit is not None
        assert blocked_audit.recovery == "retry_limit_exceeded"
    finally:
        db.close()


def test_webhook_failure_classifies_and_logs_audit():
    import hmac
    import hashlib
    db = SessionLocal()
    secret = "secret_for_failure_test"
    try:
        order = create_order(db, status="created")
        event_id = f"evt_fail_{uuid.uuid4().hex}"

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
                        "error_code": "BAD_REQUEST_PAYMENT_DECLINED",
                        "error_description": "Card was declined by issuing bank",
                        "error_reason": "payment_declined",
                    }
                }
            },
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

        result = process_webhook_payload(
            db=db,
            payload_bytes=payload_bytes,
            signature=sig,
            secret=secret,
        )

        assert result["status"] == "processed"
        assert result["order_status"] == "failed"

        db.refresh(order)
        assert order.status == "failed"

        # Verify failure was classified in audit log
        classification_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == str(order.id),
                AuditLog.action == "payment_failure_classified",
            )
            .first()
        )
        assert classification_audit is not None
        assert classification_audit.external_result == "customer-action-required"
        assert "declined" in classification_audit.error.lower()
    finally:
        db.close()
