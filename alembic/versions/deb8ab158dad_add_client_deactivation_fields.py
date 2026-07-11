"""add client deactivation fields

Revision ID: deb8ab158dad
Revises: 554732a90b6d
Create Date: 2026-03-22 12:43:15.184118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deb8ab158dad'
down_revision: Union[str, Sequence[str], None] = '554732a90b6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("fecha_desactivacion", sa.DateTime(), nullable=True))

    # ### end Alembic commands ###

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_column("fecha_desactivacion")

    # ### end Alembic commands ###
