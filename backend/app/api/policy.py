from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import Policy
from app.services.policy_service import evaluate_policy


router = APIRouter(
    prefix="/policy",
    tags=["policy"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/evaluate")
def evaluate_policy_endpoint(
    order_amount: float,
    discount: float = 0,
    confirmed: bool = False,
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy)
        .order_by(Policy.id.desc())
        .first()
    )

    if policy is None:
        policy = Policy(
            max_order_amount=100000,
            max_discount=10,
            confirmation_required=True,
            approval_threshold=90000,
        )

    decision = evaluate_policy(
        policy=policy,
        order_amount=order_amount,
        discount=discount,
        confirmed=confirmed,
    )

    return {
        "decision": decision.decision,
        "reason": decision.reason,
    }