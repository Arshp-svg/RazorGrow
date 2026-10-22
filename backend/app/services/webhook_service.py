import hashlib
import hmac
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Order, WebhookEvent
from app.services.audit_service import record_audit
from app.services.failure_service import classify_failure
from app.services.payment_service import update_payment_status


def verify_webhook_signature(
    payload_bytes: bytes,
    signature: str | None,
    secret: str | None = None,
) -> bool:
    webhook_secret = secret if secret is not None else settings.razorpay_webhook_secret

    if not webhook_secret or not signature:
        return False

    expected_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def compute_payload_hash(payload_bytes: bytes) -> str:
    return hashlib.sha256(payload_bytes).hexdigest()


def extract_event_details(
    payload: dict,
    header_event_id: str | None = None,
) -> tuple[str, str, str | None]:
    event_type = payload.get("event", "unknown")

    provider_event_id = (
        header_event_id
        or payload.get("event_id")
        or payload.get("id")
    )

    # Extract razorpay order id from standard Razorpay webhook payloads
    razorpay_order_id = (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
        .get("order_id")
        or payload.get("payload", {})
        .get("order", {})
        .get("entity", {})
        .get("id")
        or payload.get("order_id")
    )

    return provider_event_id, event_type, razorpay_order_id


def process_webhook_payload(
    db: Session,
    payload_bytes: bytes,
    signature: str | None,
    header_event_id: str | None = None,
    secret: str | None = None,
) -> dict:
    if not verify_webhook_signature(payload_bytes, signature, secret=secret):
        raise ValueError("Invalid webhook signature")

    payload_hash = compute_payload_hash(payload_bytes)

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid JSON payload") from exc

    provider_event_id, event_type, razorpay_order_id = extract_event_details(
        payload=payload,
        header_event_id=header_event_id,
    )

    if not provider_event_id:
        provider_event_id = f"evt_{payload_hash[:24]}"

    # Check for existing webhook event (idempotency check)
    existing_event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.provider_event_id == provider_event_id)
        .first()
    )

    if existing_event and existing_event.processed:
        return {
            "status": "already_processed",
            "provider_event_id": provider_event_id,
            "event_type": existing_event.event_type,
            "order_id": razorpay_order_id,
        }

    webhook_event = existing_event
    if not webhook_event:
        webhook_event = WebhookEvent(
            provider_event_id=provider_event_id,
            event_type=event_type,
            processed=False,
            payload_hash=payload_hash,
            created_at=datetime.now(timezone.utc),
        )
        db.add(webhook_event)
        db.commit()
        db.refresh(webhook_event)

    # Determine target order status
    target_status = None
    if event_type in ("payment.captured", "order.paid"):
        target_status = "paid"
    elif event_type == "payment.failed":
        target_status = "failed"

    order = None
    classification = None
    if razorpay_order_id:
        order = (
            db.query(Order)
            .filter(Order.razorpay_order_id == razorpay_order_id)
            .first()
        )

        if order and target_status:
            if order.status != target_status:
                order = update_payment_status(
                    db=db,
                    razorpay_order_id=razorpay_order_id,
                    status=target_status,
                )

        if order and event_type == "payment.failed":
            payment_entity = (
                payload.get("payload", {})
                .get("payment", {})
                .get("entity", {})
            )
            error_code = payment_entity.get("error_code") or payment_entity.get("error_reason")
            error_desc = payment_entity.get("error_description")
            classification = classify_failure(
                error_code=error_code,
                error_description=error_desc,
            )
            record_audit(
                db=db,
                merchant_id=order.merchant_id,
                action="payment_failure_classified",
                entity_id=str(order.id),
                policy_result=None,
                external_result=classification.category.value,
                error=classification.description,
                recovery=classification.suggested_action,
            )

    webhook_event.processed = True
    webhook_event.processed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(webhook_event)

    return {
        "status": "processed",
        "provider_event_id": provider_event_id,
        "event_type": event_type,
        "order_id": razorpay_order_id,
        "order_status": order.status if order else None,
    }
