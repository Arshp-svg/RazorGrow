from app.db.database import SessionLocal
from app.models.models import Policy
from app.services.policy_service import evaluate_policy


db = SessionLocal()

try:
    policy = Policy(
        max_order_amount=100000,
        max_discount=10,
        confirmation_required=True,
        approval_threshold=90000,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    decision = evaluate_policy(
    policy=policy,
    order_amount=95000,
    discount=0,
    confirmed=True,
)

    print("Decision:", decision.decision)
    print("Reason:", decision.reason)

finally:
    db.close()