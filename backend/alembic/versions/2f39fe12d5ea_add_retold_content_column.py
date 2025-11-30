"""add_retold_content_column

Revision ID: 2f39fe12d5ea
Revises: 58056bf001c3
Create Date: 2025-11-29 18:50:42.714710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f39fe12d5ea'
down_revision: Union[str, Sequence[str], None] = '58056bf001c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('articles', sa.Column('retold_content', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('articles', 'retold_content')
