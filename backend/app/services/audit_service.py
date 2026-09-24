from sqlalchemy.orm import Session

from app.models.models import AuditLog


def record_audit(
    db: Session,
    merchant_id: int,
    action: str,
    entity_id: str | None = None,
    user_id: int | None = None,
    policy_result: str | None = None,
    policy_version: int | None = None,
    external_result: str | None = None,
    error: str | None = None,
    recovery: str | None = None,
):
    audit = AuditLog(
        merchant_id=merchant_id,
        action=action,
        entity_id=entity_id,
        user_id=user_id,
        policy_result=policy_result,
        policy_version=policy_version,
        external_result=external_result,
        error=error,
        recovery=recovery,
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return audit
