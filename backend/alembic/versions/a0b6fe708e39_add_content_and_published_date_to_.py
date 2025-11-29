"""add_content_and_published_date_to_articles

Revision ID: a0b6fe708e39
Revises: 2139b197302e
Create Date: 2025-11-29 18:06:56.891015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0b6fe708e39'
down_revision: Union[str, Sequence[str], None] = '2139b197302e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('articles', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('published_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('articles', 'published_date')
    op.drop_column('articles', 'content')
