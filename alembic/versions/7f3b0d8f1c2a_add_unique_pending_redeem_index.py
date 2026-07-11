"""add unique pending redeem index

Revision ID: 7f3b0d8f1c2a
Revises: ac5c57355313
Create Date: 2026-03-24 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3b0d8f1c2a'
down_revision: Union[str, Sequence[str], None] = 'ac5c57355313'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'uq_canjes_cuenta_pendiente',
        'canjes',
        ['cuenta_id'],
        unique=True,
        sqlite_where=sa.text("estado = 'pendiente'"),
        postgresql_where=sa.text("estado = 'pendiente'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_canjes_cuenta_pendiente', table_name='canjes')
