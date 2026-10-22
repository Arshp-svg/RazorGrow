"""add_agent_executions_and_tool_calls

Revision ID: 82c595d2e6eb
Revises: 8fd6e624db7b
Create Date: 2026-10-22 22:39:56.762797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82c595d2e6eb'
down_revision: Union[str, Sequence[str], None] = '8fd6e624db7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=False),
        sa.Column('intent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='started'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_latency_ms', sa.Float(), nullable=True, server_default='0.0'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('agent_executions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_agent_executions_correlation_id'), ['correlation_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_agent_executions_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_agent_executions_merchant_id'), ['merchant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_agent_executions_session_id'), ['session_id'], unique=False)

    op.create_table(
        'tool_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='success'),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('policy_result', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['execution_id'], ['agent_executions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('tool_calls', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tool_calls_execution_id'), ['execution_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_tool_calls_id'), ['id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('tool_calls', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tool_calls_id'))
        batch_op.drop_index(batch_op.f('ix_tool_calls_execution_id'))

    op.drop_table('tool_calls')

    with op.batch_alter_table('agent_executions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_agent_executions_session_id'))
        batch_op.drop_index(batch_op.f('ix_agent_executions_merchant_id'))
        batch_op.drop_index(batch_op.f('ix_agent_executions_id'))
        batch_op.drop_index(batch_op.f('ix_agent_executions_correlation_id'))

    op.drop_table('agent_executions')
