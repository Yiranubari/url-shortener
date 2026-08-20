"""add normalized url column for dedupe

Revision ID: 06a52584c319
Revises: 8e8b477dccba
Create Date: 2026-08-20 14:53:22.444455
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '06a52584c319'
down_revision: Union[str, None] = '8e8b477dccba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('urls', sa.Column('normalized_url', sa.String(length=2048), nullable=True))
    op.execute("UPDATE urls SET normalized_url = long_url WHERE normalized_url IS NULL")
    op.alter_column('urls', 'normalized_url', nullable=False)
    op.drop_index(op.f('ix_urls_long_url'), table_name='urls')
    op.create_index(op.f('ix_urls_normalized_url'), 'urls', ['normalized_url'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_urls_normalized_url'), table_name='urls')
    op.create_index(op.f('ix_urls_long_url'), 'urls', ['long_url'], unique=True)
    op.drop_column('urls', 'normalized_url')
