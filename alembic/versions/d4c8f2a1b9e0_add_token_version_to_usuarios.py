"""add token version to usuarios

Revision ID: d4c8f2a1b9e0
Revises: 7f3b0d8f1c2a
Create Date: 2026-03-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4c8f2a1b9e0"
down_revision: Union[str, Sequence[str], None] = "7f3b0d8f1c2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("token_version", sa.Integer(), nullable=False, server_default="1")
        )

    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.alter_column("token_version", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_column("token_version")
