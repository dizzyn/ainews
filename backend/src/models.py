from sqlalchemy import Column, Integer, String, Text, DateTime
from .database import Base  # Importujeme Base z našeho database.py

class Article(Base):
    __tablename__ = "articles"  # Název tabulky v databázi

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    url = Column(String(1000), unique=True, index=True)
    categories = Column(Text, nullable=True)  # JSON string s kategorizací (země, osoby)
    content = Column(Text, nullable=True)  # Obsah článku jako markdown
    published_date = Column(DateTime, nullable=True)  # Datum vydání článku
    
    # Sumarizace
    summary_simple = Column(Text, nullable=True)  # Jednoduchá sumarizace
    summary_funny = Column(Text, nullable=True)  # Vtipná sumarizace
    summary_storytelling = Column(Text, nullable=True)  # Storytelling sumarizace
    retold_content = Column(Text, nullable=True)  # Převyprávěný obsah jako příběh
    image_filename = Column(String(255), nullable=True)  # Název vygenerovaného obrázku