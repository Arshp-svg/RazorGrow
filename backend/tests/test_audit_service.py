from app.db.database import SessionLocal
from app.services.audit_service import record_audit


db = SessionLocal()

try:
    audit = record_audit(
        db=db,
        merchant_id=3,
        action="test_event",
        entity_id="day9-test",
        policy_result="ALLOW",
        policy_version=1,
        external_result="created",
        recovery="none",
    )

    print(
        audit.id,
        audit.action,
        audit.entity_id,
        audit.policy_result,
        audit.external_result,
        audit.recovery,
    )

finally:
    db.close()
