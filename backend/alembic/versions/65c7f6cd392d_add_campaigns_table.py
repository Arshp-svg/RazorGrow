"""add_campaigns_table

Revision ID: 65c7f6cd392d
Revises: 82c595d2e6eb
Create Date: 2026-10-23 08:37:50.533095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65c7f6cd392d'
down_revision: Union[str, Sequence[str], None] = '82c595d2e6eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('bundle_config', sa.Text(), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('projected_impact', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('decided_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_campaigns_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_campaigns_merchant_id'), ['merchant_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_campaigns_merchant_id'))
        batch_op.drop_index(batch_op.f('ix_campaigns_id'))

    op.drop_table('campaigns')
