from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from app.models.models import AuditLog, Order
from app.services.audit_service import record_audit
from app.services.payment_service import update_payment_status

MAX_PAYMENT_RETRIES = 3


class FailureCategory(str, Enum):
    RETRYABLE = "retryable"
    CUSTOMER_ACTION_REQUIRED = "customer-action-required"
    INVALID_REQUEST = "invalid-request"
    POLICY_BLOCKED = "policy-blocked"


@dataclass
class FailureClassification:
    category: FailureCategory
    error_code: str
    description: str
    is_retryable: bool
    suggested_action: str


RETRYABLE_CODES = {
    "GATEWAY_ERROR",
    "SERVER_ERROR",
    "TIMEOUT_ERROR",
    "NETWORK_ERROR",
    "INTERNAL_SERVER_ERROR",
    "SERVICE_UNAVAILABLE",
    "GATEWAY_TIMEOUT",
}

CUSTOMER_ACTION_CODES = {
    "BAD_REQUEST_PAYMENT_DECLINED",
    "PAYMENT_DECLINED",
    "INSUFFICIENT_FUNDS",
    "CARD_EXPIRED",
    "EXPIRED_CARD",
    "AUTHENTICATION_FAILED",
    "INVALID_OTP",
    "OTP_EXPIRED",
    "DO_NOT_HONOR",
    "TRANSACTION_NOT_PERMITTED",
}

INVALID_REQUEST_CODES = {
    "BAD_REQUEST_ERROR",
    "INVALID_AMOUNT",
    "AMOUNT_MISMATCH",
    "INVALID_CURRENCY",
    "INVALID_ORDER_ID",
    "INVALID_PAYMENT_ID",
}

POLICY_BLOCKED_CODES = {
    "POLICY_BLOCKED",
    "LIMIT_EXCEEDED",
    "CONFIRMATION_REQUIRED",
    "APPROVAL_REQUIRED",
    "TRANSACTION_LIMIT_EXCEEDED",
}


def classify_failure(
    error_code: str | None,
    error_description: str | None = None,
    http_status: int | None = None,
) -> FailureClassification:
    normalized_code = (error_code or "").strip().upper()
    desc = error_description or "Payment operation failed"

    if normalized_code in POLICY_BLOCKED_CODES or "POLICY" in normalized_code:
        return FailureClassification(
            category=FailureCategory.POLICY_BLOCKED,
            error_code=normalized_code or "POLICY_BLOCKED",
            description=desc,
            is_retryable=False,
            suggested_action="Action exceeds merchant safety policy limits.",
        )

    if (
        normalized_code in RETRYABLE_CODES
        or (http_status is not None and http_status in (500, 502, 503, 504))
        or "TIMEOUT" in normalized_code
        or "NETWORK" in normalized_code
    ):
        return FailureClassification(
            category=FailureCategory.RETRYABLE,
            error_code=normalized_code or "GATEWAY_TIMEOUT",
            description=desc,
            is_retryable=True,
            suggested_action="Transient gateway or network error. Safe to retry with exponential backoff.",
        )

    if (
        normalized_code in CUSTOMER_ACTION_CODES
        or "DECLINED" in normalized_code
        or "FUNDS" in normalized_code
        or "OTP" in normalized_code
        or (http_status == 402)
    ):
        return FailureClassification(
            category=FailureCategory.CUSTOMER_ACTION_REQUIRED,
            error_code=normalized_code or "PAYMENT_DECLINED",
            description=desc,
            is_retryable=True,
            suggested_action="Customer action required: please verify payment details or select another payment method.",
        )

    # Default to invalid-request for client/validation errors
    return FailureClassification(
        category=FailureCategory.INVALID_REQUEST,
        error_code=normalized_code or "BAD_REQUEST_ERROR",
        description=desc,
        is_retryable=False,
        suggested_action="Invalid request payload or configuration. Please check parameters.",
    )


def get_order_retry_count(db: Session, order_id: int) -> int:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_id == str(order_id),
            AuditLog.action == "payment_retry_attempted",
        )
        .count()
    )


def can_retry_payment(
    db: Session,
    order: Order,
    max_retries: int = MAX_PAYMENT_RETRIES,
) -> tuple[bool, str, int]:
    if order.status == "paid":
        return False, "Order is already paid.", 0

    if order.status != "failed":
        return (
            False,
            f"Order payment status is '{order.status}'. Retry only allowed from 'failed' status.",
            0,
        )

    current_retries = get_order_retry_count(db, order.id)

    if current_retries >= max_retries:
        record_audit(
            db=db,
            merchant_id=order.merchant_id,
            action="payment_retry_blocked",
            entity_id=str(order.id),
            policy_result=None,
            external_result="blocked",
            error=f"Maximum retry attempts ({max_retries}) exceeded.",
            recovery="retry_limit_exceeded",
        )
        return (
            False,
            f"Maximum retry attempts ({max_retries}) exceeded. No further retries allowed.",
            current_retries,
        )

    return True, "Retry permitted.", current_retries


def execute_payment_retry(
    db: Session,
    order: Order,
    target_status: str = "paid",
    error_code: str | None = None,
    error_description: str | None = None,
    max_retries: int = MAX_PAYMENT_RETRIES,
) -> dict:
    allowed, reason, retry_count = can_retry_payment(
        db=db,
        order=order,
        max_retries=max_retries,
    )

    if not allowed:
        raise ValueError(reason)

    new_retry_count = retry_count + 1

    # Record the retry attempt in the audit trail
    record_audit(
        db=db,
        merchant_id=order.merchant_id,
        action="payment_retry_attempted",
        entity_id=str(order.id),
        policy_result=None,
        external_result=f"attempt_{new_retry_count}",
        error=None,
        recovery=f"attempt_{new_retry_count}_of_{max_retries}",
    )

    if target_status == "paid":
        order = update_payment_status(
            db=db,
            razorpay_order_id=order.razorpay_order_id,
            status="paid",
        )

        return {
            "status": "paid",
            "order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "retry_count": new_retry_count,
            "recovery": "recovered",
        }

    # If the retry failed again (e.g. simulated controlled failure or gateway decline)
    classification = classify_failure(
        error_code=error_code or "PAYMENT_DECLINED",
        error_description=error_description or "Payment retry was declined",
    )

    remaining_retries = max_retries - new_retry_count
    recovery_status = (
        "retry_available" if remaining_retries > 0 else "retry_limit_exceeded"
    )

    record_audit(
        db=db,
        merchant_id=order.merchant_id,
        action="payment_retry_failed",
        entity_id=str(order.id),
        policy_result=None,
        external_result="failed",
        error=classification.description,
        recovery=recovery_status,
    )

    return {
        "status": "failed",
        "order_id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "category": classification.category.value,
        "error_code": classification.error_code,
        "suggested_action": classification.suggested_action,
        "retry_count": new_retry_count,
        "recovery": recovery_status,
    }
