"""update loyalty relationships and cascades

Revision ID: 554732a90b6d
Revises: b7a86f0c56d5
Create Date: 2026-03-22 12:27:33.195190

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '554732a90b6d'
down_revision: Union[str, Sequence[str], None] = 'b7a86f0c56d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
