import os
import time
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import google.generativeai as genai
from .database import SessionLocal
from .models import Article

load_dotenv()

# Konfigurace
DELAY_BETWEEN_ARTICLES = float(os.getenv("DELAY_BETWEEN_ARTICLES", "2"))

# Inicializace Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_embedding_for_article(article: Article, db: Session) -> bool:
    """
    Vygeneruje embedding pro daný článek na základě jeho sumarizace.
    Vrací True pokud byl embedding úspěšně vygenerován.
    """
    if not article.summary_simple:
        print(f"Článek {article.id} nemá sumarizaci, přeskakuji")
        return False
    
    # Pokud už má embedding, přeskočíme
    if article.embedding is not None:
        print(f"Článek {article.id} už má embedding")
        return False
    
    print(f"Generuji embedding pro článek {article.id}: {article.title}")
    
    try:
        # Vytvoříme text pro embedding z titulku a sumarizace
        text_for_embedding = f"{article.title}\n\n{article.summary_simple}"
        
        # Vygenerujeme embedding pomocí Gemini
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text_for_embedding,
            task_type="retrieval_document"
        )
        
        # Uložíme embedding do databáze (konverze numpy array na list)
        embedding_vector = result['embedding']
        if hasattr(embedding_vector, 'tolist'):
            embedding_vector = embedding_vector.tolist()
        article.embedding = embedding_vector
        db.commit()
        
        print(f"  ✓ Embedding vygenerován (dimenze: {len(result['embedding'])})")
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Přerušeno uživatelem")
        db.rollback()
        raise
    except Exception as e:
        print(f"✗ Chyba při generování embeddingu pro článek {article.id}: {e}")
        db.rollback()
        return False


def process_all_articles():
    """
    Projde všechny články v databázi a vygeneruje pro ně embeddingy.
    """
    db = SessionLocal()
    try:
        # Načteme všechny články kromě digestu
        articles = db.query(Article).filter(Article.url != "DIGEST").all()
        print(f"Nalezeno {len(articles)} článků")
        
        processed = 0
        skipped = 0
        errors = 0
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}]")
            result = generate_embedding_for_article(article, db)
            if result:
                processed += 1
                # Pauza mezi články
                if i < len(articles):
                    time.sleep(DELAY_BETWEEN_ARTICLES)
            elif article.embedding is not None:
                skipped += 1
            else:
                errors += 1
        
        print(f"\n=== Hotovo ===")
        print(f"Zpracováno: {processed}")
        print(f"Přeskočeno (už má embedding): {skipped}")
        print(f"Chyby: {errors}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("Spouštím generování embeddingů...")
    process_all_articles()
