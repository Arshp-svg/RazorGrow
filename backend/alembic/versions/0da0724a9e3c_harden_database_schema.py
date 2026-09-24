"""harden database schema

Revision ID: 0da0724a9e3c
Revises:
Create Date: 2026-09-20 19:59:23.553228
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0da0724a9e3c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return inspect(bind).has_table(name)


def _create_fresh_schema() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("settings", sa.Text(), nullable=True),
    )
    op.create_index("ix_merchants_id", "merchants", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "merchant_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "ix_merchant_memberships_id",
        "merchant_memberships",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_merchant_memberships_merchant_id",
        "merchant_memberships",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_merchant_memberships_user_id",
        "merchant_memberships",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("tags", sa.String(500), nullable=False),
        sa.Column("use_cases", sa.String(500), nullable=False),
        sa.Column("compatible_products", sa.String(500), nullable=False),
        sa.Column("upsell_products", sa.String(500), nullable=False),
        sa.Column("inventory", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index(
        "ix_products_merchant_id",
        "products",
        ["merchant_id"],
        unique=False,
    )

    op.create_table(
        "carts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
    )
    op.create_index("ix_carts_id", "carts", ["id"], unique=False)
    op.create_index(
        "ix_carts_merchant_id",
        "carts",
        ["merchant_id"],
        unique=False,
    )

    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index(
        "ix_cart_items_id",
        "cart_items",
        ["id"],
        unique=False,
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("razorpay_order_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
    )
    op.create_index("ix_orders_id", "orders", ["id"], unique=False)
    op.create_index(
        "ix_orders_merchant_id",
        "orders",
        ["merchant_id"],
        unique=False,
    )

    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("max_order_amount", sa.Float(), nullable=False),
        sa.Column("max_discount", sa.Float(), nullable=False),
        sa.Column("confirmation_required", sa.Boolean(), nullable=False),
        sa.Column("approval_threshold", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
    )
    op.create_index("ix_policies_id", "policies", ["id"], unique=False)
    op.create_index(
        "ix_policies_merchant_id",
        "policies",
        ["merchant_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("policy_result", sa.String(50), nullable=True),
        sa.Column("external_result", sa.String(255), nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
        sa.Column("recovery", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"], unique=False)
    op.create_index(
        "ix_audit_logs_merchant_id",
        "audit_logs",
        ["merchant_id"],
        unique=False,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "ix_refresh_tokens_id",
        "refresh_tokens",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )


def _harden_existing_mvp_schema() -> None:
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.add_column(
            sa.Column("merchant_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_audit_logs_merchant_id",
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_audit_logs_merchant_id",
            "merchants",
            ["merchant_id"],
            ["id"],
        )

    with op.batch_alter_table("carts") as batch_op:
        batch_op.add_column(
            sa.Column("merchant_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_carts_merchant_id",
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_carts_merchant_id",
            "merchants",
            ["merchant_id"],
            ["id"],
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(
            sa.Column("merchant_id", sa.Integer(), nullable=True)
        )
        batch_op.alter_column(
            "cart_id",
            existing_type=sa.INTEGER(),
            nullable=False,
        )
        batch_op.create_index(
            "ix_orders_merchant_id",
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_orders_cart_id",
            "carts",
            ["cart_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_orders_merchant_id",
            "merchants",
            ["merchant_id"],
            ["id"],
        )

    with op.batch_alter_table("policies") as batch_op:
        batch_op.add_column(
            sa.Column("merchant_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_policies_merchant_id",
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_policies_merchant_id",
            "merchants",
            ["merchant_id"],
            ["id"],
        )

    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(
            sa.Column("merchant_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_products_merchant_id",
            ["merchant_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_products_merchant_id",
            "merchants",
            ["merchant_id"],
            ["id"],
        )


def upgrade() -> None:
    if not _table_exists("merchants"):
        _create_fresh_schema()
    else:
        _harden_existing_mvp_schema()


def downgrade() -> None:
    if _table_exists("refresh_tokens"):
        op.drop_table("refresh_tokens")
    if _table_exists("audit_logs"):
        op.drop_table("audit_logs")
    if _table_exists("policies"):
        op.drop_table("policies")
    if _table_exists("orders"):
        op.drop_table("orders")
    if _table_exists("cart_items"):
        op.drop_table("cart_items")
    if _table_exists("carts"):
        op.drop_table("carts")
    if _table_exists("products"):
        op.drop_table("products")
    if _table_exists("merchant_memberships"):
        op.drop_table("merchant_memberships")
    if _table_exists("users"):
        op.drop_table("users")
    if _table_exists("merchants"):
        op.drop_table("merchants")
