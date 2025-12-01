from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pathlib import Path
import google.generativeai as genai
import os

from . import models, schemas
from .database import engine, get_db, Base

# Konfigurace Gemini pro embeddingy
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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


@app.get("/digest/", response_model=schemas.ArticleDetail, tags=["Articles"])
def read_digest(db: Session = Depends(get_db)):
    """
    Vrátí aktuální přehled zpráv (digest).
    """
    digest = db.query(models.Article).filter(models.Article.url == "DIGEST").first()
    if digest is None:
        raise HTTPException(status_code=404, detail="Přehled zpráv nenalezen")
    return digest


@app.get("/articles/", response_model=List[schemas.Article], tags=["Articles"])
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Vrátí seznam článků (bez digestu).
    """
    articles = db.query(models.Article).filter(models.Article.url != "DIGEST").offset(skip).limit(limit).all()
    return articles


@app.get("/articles/{article_id}", response_model=schemas.ArticleDetail, tags=["Articles"])
def read_article(article_id: int, db: Session = Depends(get_db)):
    """
    Vrátí detail článku včetně obsahu.
    """
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Článek nenalezen")
    return article


@app.get("/images/{filename}", tags=["Images"])
def get_image(filename: str):
    """
    Vrátí obrázek článku.
    """
    image_path = Path("backend/static/images") / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Obrázek nenalezen")
    return FileResponse(image_path)


@app.get("/articles/{article_id}/related", response_model=List[schemas.Article], tags=["Articles"])
def get_related_articles(article_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """
    Vrátí podobné články pomocí RAG (vektorové podobnosti).
    """
    # Načteme článek
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Článek nenalezen")
    
    # Pokud článek nemá embedding, nemůžeme najít podobné
    if article.embedding is None:
        return []
    
    # Konvertujeme embedding na list (pokud je to numpy array)
    embedding_list = article.embedding
    if hasattr(embedding_list, 'tolist'):
        embedding_list = embedding_list.tolist()
    
    # Najdeme podobné články pomocí cosine similarity
    # Používáme pgvector operátor <=> pro cosine distance
    query = text("""
        SELECT id, title, url, categories
        FROM articles
        WHERE id != :article_id 
        AND embedding IS NOT NULL
        AND url != 'DIGEST'
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)
    
    result = db.execute(
        query,
        {
            "article_id": article_id,
            "embedding": embedding_list,
            "limit": limit
        }
    )
    
    # Převedeme výsledky na Article objekty
    related = []
    for row in result:
        related.append(schemas.Article(
            id=row.id,
            title=row.title,
            url=row.url,
            categories=row.categories
        ))
    
    return related