from fastapi import APIRouter
from app.models.models import AuditLog
from app.db.database import SessionLocal
from app.services.dashboard_service import get_dashboard_metrics
from app.models.models import AuditLog, Order

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

@router.get("/status")
def dashboard_status():
    db = SessionLocal()

    try:
        return {
            "agent": "operational",
            "database": "connected",
            "policy_engine": "operational",
            "payment_service": "operational",
            "audit_logging": "operational",
        }

    finally:
        db.close()
        
@router.get("/metrics")
def dashboard_metrics():
    db = SessionLocal()

    try:
        return get_dashboard_metrics(db)

    finally:
        db.close()
        
        
@router.get("/activity")
def dashboard_activity(limit: int = 20):
    db = SessionLocal()

    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": log.id,
                "action": log.action,
                "entity_id": log.entity_id,
                "policy_result": log.policy_result,
                "external_result": log.external_result,
                "error": log.error,
                "recovery": log.recovery,
            }
            for log in logs
        ]

    finally:
        db.close()
        

@router.get("/overview")
def dashboard_overview(limit: int = 20):
    db = SessionLocal()

    try:
        metrics = get_dashboard_metrics(db)

        logs = (
            db.query(AuditLog)
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
            }
            for log in logs
        ]

        return {
            "metrics": metrics,
            "activity": activity,
        }

    finally:
        db.close()
        
        
@router.get("/orders")
def dashboard_orders(limit: int = 20):
    db = SessionLocal()

    try:
        orders = (
            db.query(Order)
            .order_by(Order.id.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": order.id,
                "cart_id": order.cart_id,
                "amount": order.amount,
                "status": order.status,
                "razorpay_order_id": order.razorpay_order_id,
            }
            for order in orders
        ]

    finally:
        db.close()