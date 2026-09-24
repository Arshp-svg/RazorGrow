import pytest

from app.models.models import Policy
from app.services.policy_service import evaluate_policy


def make_policy(**overrides):
    values = {
        "max_order_amount": 100000,
        "max_discount": 10,
        "confirmation_required": True,
        "approval_threshold": 90000,
    }
    values.update(overrides)
    return Policy(**values)


def test_policy_approves_valid_order():
    decision = evaluate_policy(
        policy=make_policy(),
        order_amount=50000,
        discount=5,
        confirmed=True,
    )

    assert decision.decision == "ALLOW"


def test_policy_blocks_amount_over_limit():
    decision = evaluate_policy(
        policy=make_policy(max_order_amount=100000),
        order_amount=100001,
        confirmed=True,
    )

    assert decision.decision == "BLOCK"


def test_policy_blocks_discount_over_limit():
    decision = evaluate_policy(
        policy=make_policy(max_discount=10),
        order_amount=50000,
        discount=11,
        confirmed=True,
    )

    assert decision.decision == "BLOCK"


def test_policy_blocks_when_confirmation_is_required():
    decision = evaluate_policy(
        policy=make_policy(confirmation_required=True),
        order_amount=50000,
        discount=0,
        confirmed=False,
    )

    assert decision.decision == "BLOCK"


def test_policy_requires_approval_at_threshold():
    decision = evaluate_policy(
        policy=make_policy(approval_threshold=90000),
        order_amount=90000,
        discount=0,
        confirmed=True,
    )

    assert decision.decision == "NEEDS_APPROVAL"


def test_policy_allows_amount_below_approval_threshold():
    decision = evaluate_policy(
        policy=make_policy(approval_threshold=90000),
        order_amount=89999,
        discount=0,
        confirmed=True,
    )

    assert decision.decision == "ALLOW"
