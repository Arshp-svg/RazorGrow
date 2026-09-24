from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth_dependencies import (
    get_current_merchant_context,
    require_merchant_roles,
)
from app.auth.roles import MerchantRole
from app.db.database import SessionLocal
from app.models.models import ApprovalRequest
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalRequestResponse,
)
from app.services.audit_service import record_audit

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    response_model=list[ApprovalRequestResponse],
)
def list_approval_requests(
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]

    return (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.merchant_id == merchant.id)
        .order_by(ApprovalRequest.id.desc())
        .all()
    )


def decide_approval(
    approval_id: int,
    decision: str,
    request: ApprovalDecisionRequest,
    db: Session,
    merchant_context,
):
    merchant, user = merchant_context

    approval = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.merchant_id == merchant.id,
        )
        .first()
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found",
        )

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Approval request has already been decided",
        )

    now = datetime.utcnow()

    if approval.expires_at is not None and approval.expires_at <= now:
        approval.status = "EXPIRED"
        approval.decided_at = now
        approval.decision_reason = "Approval request expired"

        db.commit()
        db.refresh(approval)

        raise HTTPException(
            status_code=409,
            detail="Approval request has expired",
        )

    approval.status = decision
    approval.decided_at = now
    approval.decided_by_user_id = user.id
    approval.decision_reason = request.reason

    db.commit()
    db.refresh(approval)

    record_audit(
        db=db,
        merchant_id=merchant.id,
        action=f"approval_{decision.lower()}",
        entity_id=str(approval.order_id),
        user_id=user.id,
        policy_result="NEEDS_APPROVAL",
        policy_version=None,
        external_result=None,
        error=None,
        recovery=None,
    )

    return approval


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalRequestResponse,
)
def approve_approval_request(
    approval_id: int,
    request: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    merchant_context=Depends(
        require_merchant_roles(
            MerchantRole.OWNER,
            MerchantRole.ADMIN,
            MerchantRole.OPERATOR,
        )
    ),
):
    return decide_approval(
        approval_id=approval_id,
        decision="APPROVED",
        request=request,
        db=db,
        merchant_context=merchant_context,
    )


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalRequestResponse,
)
def reject_approval_request(
    approval_id: int,
    request: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    merchant_context=Depends(
        require_merchant_roles(
            MerchantRole.OWNER,
            MerchantRole.ADMIN,
            MerchantRole.OPERATOR,
        )
    ),
):
    return decide_approval(
        approval_id=approval_id,
        decision="REJECTED",
        request=request,
        db=db,
        merchant_context=merchant_context,
    )
