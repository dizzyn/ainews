from sqlalchemy import Column, Integer, String, Text
from .database import Base  # Importujeme Base z našeho database.py

class Article(Base):
    __tablename__ = "articles"  # Název tabulky v databázi

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    url = Column(String(1000), unique=True, index=True)
    categories = Column(Text, nullable=True)  # JSON string s kategorizací (země, osoby)