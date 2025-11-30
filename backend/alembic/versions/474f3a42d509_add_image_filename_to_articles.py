"""add_image_filename_to_articles

Revision ID: 474f3a42d509
Revises: 2f39fe12d5ea
Create Date: 2025-11-29 18:57:38.126615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '474f3a42d509'
down_revision: Union[str, Sequence[str], None] = '2f39fe12d5ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('articles', sa.Column('image_filename', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('articles', 'image_filename')
