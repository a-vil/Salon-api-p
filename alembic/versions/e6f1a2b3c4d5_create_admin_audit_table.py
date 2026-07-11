"""create admin audit table

Revision ID: e6f1a2b3c4d5
Revises: d4c8f2a1b9e0
Create Date: 2026-03-31 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "d4c8f2a1b9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auditoria_admin",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
        sa.Column("admin_identificador", sa.String(length=120), nullable=False),
        sa.Column("accion", sa.String(length=60), nullable=False),
        sa.Column("entidad", sa.String(length=60), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auditoria_admin_created_at",
        "auditoria_admin",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_auditoria_admin_entidad_entidad_id",
        "auditoria_admin",
        ["entidad", "entidad_id"],
        unique=False,
    )
    op.create_index(
        "ix_auditoria_admin_admin_user_id",
        "auditoria_admin",
        ["admin_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_auditoria_admin_admin_user_id", table_name="auditoria_admin")
    op.drop_index("ix_auditoria_admin_entidad_entidad_id", table_name="auditoria_admin")
    op.drop_index("ix_auditoria_admin_created_at", table_name="auditoria_admin")
    op.drop_table("auditoria_admin")
