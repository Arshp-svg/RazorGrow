"""add policy version to audit logs

Revision ID: cac6d143bb80
Revises: add6e96a65d1
Create Date: 2026-09-22 20:12:14.269601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cac6d143bb80'
down_revision: Union[str, Sequence[str], None] = 'add6e96a65d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "audit_logs",
        sa.Column("policy_version", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("audit_logs", "policy_version")
