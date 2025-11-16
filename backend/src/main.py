from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List # Přidat tento import

from . import models, schemas
from .database import engine, get_db, Base

# Tento příkaz řekne Alembicu o našich modelech.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Article Admin API",
    version="0.1.0"
)

# --- Nastavení CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", # SvelteKit
        "http://localhost",       # Nginx
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Vítej v Article Admin API!"}


# --- API Endpointy pro Články ---

@app.post("/articles/", response_model=schemas.Article, tags=["Articles"])
def create_article(
    article: schemas.ArticleCreate, 
    db: Session = Depends(get_db)
):
    """
    Vytvoří nový článek v databázi.
    """
    db_article = models.Article(
        title=article.title, 
        content=article.content
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article) # Získáme zpět ID, které vygenerovala DB
    return db_article


@app.get("/articles/", response_model=List[schemas.Article], tags=["Articles"])
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Vrátí seznam článků.
    """
    articles = db.query(models.Article).offset(skip).limit(limit).all()
    return articles