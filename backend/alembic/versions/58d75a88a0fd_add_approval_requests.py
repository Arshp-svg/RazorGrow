"""add approval requests

Revision ID: 58d75a88a0fd
Revises: cac6d143bb80
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "58d75a88a0fd"
down_revision: Union[str, Sequence[str], None] = "cac6d143bb80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decision_reason", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("approval_requests", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_approval_requests_id"),
            ["id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_approval_requests_merchant_id"),
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_approval_requests_order_id"),
            ["order_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("approval_requests", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_approval_requests_order_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_approval_requests_merchant_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_approval_requests_id")
        )

    op.drop_table("approval_requests")
