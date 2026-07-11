"""add usuarios table

Revision ID: 3595e4aea5fc
Revises: deb8ab158dad
Create Date: 2026-03-23 11:48:04.593919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3595e4aea5fc'
down_revision: Union[str, Sequence[str], None] = 'deb8ab158dad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('correo', sa.String(length=120), nullable=True),
        sa.Column('celular', sa.String(length=20), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('rol', sa.String(length=20), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('celular'),
        sa.UniqueConstraint('cliente_id'),
        sa.UniqueConstraint('correo')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('usuarios')
