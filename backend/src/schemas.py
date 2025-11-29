from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Základní schéma s poli, která jsou společná
class ArticleBase(BaseModel):
    title: str
    url: str
    categories: Optional[str] = None

# Schéma pro Vytvoření článku (co přijímáme od klienta)
class ArticleCreate(ArticleBase):
    pass  # Zatím je stejné jako ArticleBase

# Schéma pro Čtení článku (co vracíme klientovi)
# Bude obsahovat i 'id', které generuje databáze
class Article(ArticleBase):
    id: int

    # Říká Pydanticu, aby četl data i z ORM modelu (nejen z dict)
    class Config:
        from_attributes = True

# Schéma pro detail článku s obsahem
class ArticleDetail(ArticleBase):
    id: int
    content: Optional[str] = None
    published_date: Optional[datetime] = None

    class Config:
        from_attributes = True