"""Initial database schema

Revision ID: 0001
Revises:
Create Date: 2026-07-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("preferred_language", sa.Text(), nullable=True),
        sa.Column("is_admin", sa.Integer(), server_default="0"),
        sa.Column("message_count", sa.Integer(), server_default="0"),
        sa.Column("escalation_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("last_seen_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )
    op.create_table(
        "analytics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "support_tickets",
        sa.Column("ticket_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="open"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("order_id", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.Text(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("resolved_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )
    op.create_table(
        "csat_ratings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("csat_ratings")
    op.drop_table("support_tickets")
    op.drop_table("analytics")
    op.drop_table("messages")
    op.drop_table("users")
