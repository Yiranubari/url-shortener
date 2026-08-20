"""add unique index on long url

Revision ID: 8e8b477dccba
Revises: 4482ed111fc6
Create Date: 2026-08-20 14:19:12.263478
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8e8b477dccba'
down_revision: Union[str, None] = '4482ed111fc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_urls_long_url'), 'urls', ['long_url'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_urls_long_url'), table_name='urls')
