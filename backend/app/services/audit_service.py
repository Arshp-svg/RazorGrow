from sqlalchemy.orm import Session

from app.models.models import AuditLog


def record_audit(
    db: Session,
    action: str,
    entity_id: str | None = None,
    policy_result: str | None = None,
    external_result: str | None = None,
    error: str | None = None,
    recovery: str | None = None,
):
    audit = AuditLog(
        action=action,
        entity_id=entity_id,
        policy_result=policy_result,
        external_result=external_result,
        error=error,
        recovery=recovery,
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return audit 