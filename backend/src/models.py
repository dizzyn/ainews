from sqlalchemy import Column, Integer, String, Text
from .database import Base  # Importujeme Base z našeho database.py

class Article(Base):
    __tablename__ = "articles"  # Název tabulky v databázi

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text, nullable=True)
    # Později můžeš přidat další, např. 'author', 'created_at' atd.