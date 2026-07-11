"""update redeems flow

Revision ID: ac5c57355313
Revises: 3595e4aea5fc
Create Date: 2026-03-24 13:49:16.228838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac5c57355313'
down_revision: Union[str, Sequence[str], None] = '3595e4aea5fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("canjes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1")
        )

    with op.batch_alter_table("canjes", schema=None) as batch_op:
        batch_op.alter_column("cantidad", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("canjes", schema=None) as batch_op:
        batch_op.drop_column("cantidad")
