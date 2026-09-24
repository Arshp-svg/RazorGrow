"""add policy versioning

Revision ID: add6e96a65d1
Revises: 0da0724a9e3c
Create Date: 2026-09-21 22:47:09.856594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add6e96a65d1'
down_revision: Union[str, Sequence[str], None] = '0da0724a9e3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "policies",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("policies", "version")

