"""remove_imagen_micro

Revision ID: f6a3400530a8
Revises: 7f4c2d1e8b10
Create Date: 2026-07-02 07:40:52.747348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a3400530a8'
down_revision: Union[str, None] = '7f4c2d1e8b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('lineas', 'imagen_micro')


def downgrade() -> None:
    op.add_column('lineas', sa.Column('imagen_micro', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
