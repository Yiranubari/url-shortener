"""create urls table

Revision ID: 4482ed111fc6
Revises: 
Create Date: 2026-08-20 13:54:12.026111
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4482ed111fc6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('urls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('short_code', sa.String(length=16), nullable=False),
    sa.Column('long_url', sa.String(length=2048), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_urls_short_code'), 'urls', ['short_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_urls_short_code'), table_name='urls')
    op.drop_table('urls')
