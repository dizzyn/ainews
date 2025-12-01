"""add_pgvector_and_embedding

Revision ID: 5a8c9d3e1f2b
Revises: 474f3a42d509
Create Date: 2025-12-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '5a8c9d3e1f2b'
down_revision: Union[str, Sequence[str], None] = '474f3a42d509'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Aktivujeme pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Přidáme sloupec pro embedding (768 dimenzí pro Gemini text-embedding-004)
    op.add_column('articles', sa.Column('embedding', Vector(768), nullable=True))
    
    # Vytvoříme index pro rychlejší vyhledávání
    op.execute('CREATE INDEX ON articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('articles', 'embedding')
    # Extension necháme, může být používána jinde
