"""add order idempotency key

Revision ID: 12e40a8601eb
Revises: e92ed94a65db
Create Date: 2026-09-26 21:46:18.363369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "12e40a8601eb"
down_revision: Union[str, Sequence[str], None] = "e92ed94a65db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add and backfill order idempotency keys."""

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "idempotency_key",
                sa.String(length=255),
                nullable=True,
            )
        )

    connection = op.get_bind()

    orders = sa.table(
        "orders",
        sa.column("id", sa.Integer),
        sa.column("idempotency_key", sa.String(length=255)),
    )

    connection.execute(
        orders.update()
        .where(orders.c.idempotency_key.is_(None))
        .values(
    idempotency_key=sa.literal("legacy-order-") + sa.cast(
        orders.c.id,
        sa.String,
    )
)
    )

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.alter_column(
            "idempotency_key",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_orders_merchant_id_idempotency_key",
            ["merchant_id", "idempotency_key"],
        )


def downgrade() -> None:
    """Remove order idempotency keys."""

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_orders_merchant_id_idempotency_key",
            type_="unique",
        )
        batch_op.drop_column("idempotency_key")