from pydantic import BaseModel
from typing import Optional

# Základní schéma s poli, která jsou společná
class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None

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