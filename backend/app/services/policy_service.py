from dataclasses import dataclass

from app.models.models import Policy


@dataclass
class PolicyDecision:
    decision: str
    reason: str


def evaluate_policy(
    policy: Policy,
    order_amount: float,
    discount: float = 0,
    confirmed: bool = False,
) -> PolicyDecision:

    if order_amount > policy.max_order_amount:
        return PolicyDecision(
            decision="BLOCKED",
            reason=(
                "Order amount exceeds the maximum "
                "allowed transaction amount."
            ),
        )

    if discount > policy.max_discount:
        return PolicyDecision(
            decision="BLOCKED",
            reason=(
                "Requested discount exceeds the "
                "maximum allowed discount."
            ),
        )

    if policy.confirmation_required and not confirmed:
        return PolicyDecision(
            decision="BLOCKED",
            reason=(
                "Customer confirmation is required "
                "before proceeding."
            ),
        )

    if (
        policy.approval_threshold is not None
        and order_amount >= policy.approval_threshold
    ):
        return PolicyDecision(
            decision="NEEDS_APPROVAL",
            reason=(
                "Order amount requires additional "
                "approval."
            ),
        )

    return PolicyDecision(
        decision="APPROVED",
        reason="Order satisfies all merchant policies.",
    )