"""create sessions table

Revision ID: f9a7c6d5e4b3
Revises: e6f1a2b3c4d5
Create Date: 2026-03-31 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f9a7c6d5e4b3"
down_revision: Union[str, Sequence[str], None] = "e6f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sesiones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("ip_creacion", sa.String(length=45), nullable=True),
        sa.Column("user_agent_creacion", sa.String(length=255), nullable=True),
        sa.Column("ip_ultima_actividad", sa.String(length=45), nullable=True),
        sa.Column("user_agent_ultima_actividad", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sesiones_estado", "sesiones", ["estado"], unique=False)
    op.create_index("ix_sesiones_expires_at", "sesiones", ["expires_at"], unique=False)
    op.create_index("ix_sesiones_session_token_hash", "sesiones", ["session_token_hash"], unique=True)
    op.create_index("ix_sesiones_user_id", "sesiones", ["user_id"], unique=False)
    op.create_index(
        "uq_sesiones_user_id_activa",
        "sesiones",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("estado = 'activa'"),
        postgresql_where=sa.text("estado = 'activa'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_sesiones_user_id", table_name="sesiones")
    op.drop_index("ix_sesiones_session_token_hash", table_name="sesiones")
    op.drop_index("ix_sesiones_expires_at", table_name="sesiones")
    op.drop_index("ix_sesiones_estado", table_name="sesiones")
    op.drop_index("uq_sesiones_user_id_activa", table_name="sesiones")
    op.drop_table("sesiones")
