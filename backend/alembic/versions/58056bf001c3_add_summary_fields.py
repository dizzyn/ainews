"""add_summary_fields

Revision ID: 58056bf001c3
Revises: a0b6fe708e39
Create Date: 2025-11-29 18:35:19.525865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58056bf001c3'
down_revision: Union[str, Sequence[str], None] = 'a0b6fe708e39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('articles', sa.Column('summary_simple', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('summary_funny', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('summary_storytelling', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('articles', 'summary_storytelling')
    op.drop_column('articles', 'summary_funny')
    op.drop_column('articles', 'summary_simple')
