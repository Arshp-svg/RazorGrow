from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth_dependencies import (
    get_current_merchant_context,
    require_merchant_roles,
)
from app.auth.roles import MerchantRole
from app.db.database import SessionLocal
from app.models.models import AuditLog
from app.services.analytics_service import (
    decide_campaign,
    generate_revenue_insights,
    get_agent_metrics,
    get_revenue_metrics,
    list_campaigns,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/overview")
def analytics_overview(
    limit: int = 20,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    metrics = get_revenue_metrics(db, merchant_id=merchant.id)
    agent = get_agent_metrics(db, merchant_id=merchant.id)

    recent_logs = (
        db.query(AuditLog)
        .filter(AuditLog.merchant_id == merchant.id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
        .all()
    )

    activity = [
        {
            "id": log.id,
            "action": log.action,
            "entity_id": log.entity_id,
            "policy_result": log.policy_result,
            "external_result": log.external_result,
            "error": log.error,
            "recovery": log.recovery,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in recent_logs
    ]

    return {
        "metrics": metrics,
        "agent": agent,
        "activity": activity,
    }


@router.get("/revenue")
def analytics_revenue(
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    return get_revenue_metrics(db, merchant_id=merchant.id)


@router.get("/agent")
def analytics_agent(
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    return get_agent_metrics(db, merchant_id=merchant.id)


@router.post("/insights")
def analytics_insights(
    db: Session = Depends(get_db),
    merchant_context=Depends(
        require_merchant_roles(
            MerchantRole.OWNER,
            MerchantRole.ADMIN,
            MerchantRole.OPERATOR,
        )
    ),
):
    merchant = merchant_context[0]
    return generate_revenue_insights(db, merchant_id=merchant.id)


@router.get("/campaigns")
def get_merchant_campaigns(
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    return list_campaigns(db, merchant_id=merchant.id)


@router.post("/campaigns/{campaign_id}/approve")
def approve_campaign_route(
    campaign_id: int,
    db: Session = Depends(get_db),
    merchant_context=Depends(
        require_merchant_roles(
            MerchantRole.OWNER,
            MerchantRole.ADMIN,
        )
    ),
):
    merchant, membership = merchant_context
    try:
        campaign = decide_campaign(
            db=db,
            campaign_id=campaign_id,
            merchant_id=merchant.id,
            user_id=membership.user_id,
            approve=True,
        )
        return {
            "status": "ok",
            "campaign_id": campaign.id,
            "campaign_status": campaign.status,
            "message": "Campaign approved and activated successfully.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/campaigns/{campaign_id}/reject")
def reject_campaign_route(
    campaign_id: int,
    db: Session = Depends(get_db),
    merchant_context=Depends(
        require_merchant_roles(
            MerchantRole.OWNER,
            MerchantRole.ADMIN,
        )
    ),
):
    merchant, membership = merchant_context
    try:
        campaign = decide_campaign(
            db=db,
            campaign_id=campaign_id,
            merchant_id=merchant.id,
            user_id=membership.user_id,
            approve=False,
        )
        return {
            "status": "ok",
            "campaign_id": campaign.id,
            "campaign_status": campaign.status,
            "message": "Campaign proposal rejected.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
