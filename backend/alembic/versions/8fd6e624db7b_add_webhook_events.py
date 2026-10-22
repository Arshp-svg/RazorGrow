"""add webhook events

Revision ID: 8fd6e624db7b
Revises: 12e40a8601eb
Create Date: 2026-10-06 14:18:09.408932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8fd6e624db7b"
down_revision: Union[str, Sequence[str], None] = "12e40a8601eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "provider_event_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "processed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "payload_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "provider_event_id",
            name="uq_webhook_events_provider_event_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")
