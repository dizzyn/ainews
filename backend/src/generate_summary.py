import os
import time
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from .database import SessionLocal
from .models import Article

load_dotenv()

# Načtení konfigurace
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
DELAY_BETWEEN_ARTICLES = float(os.getenv("DELAY_BETWEEN_ARTICLES", "2"))

# Inicializace LLM
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7,
    max_retries=3
)

def generate_summaries_for_article(article: Article, db: Session) -> bool:
    """
    Vygeneruje pouze jednoduchou sumarizaci pro daný článek.
    Vrací True pokud byla sumarizace úspěšně vygenerována.
    """
    if not article.content:
        print(f"Článek {article.id} nemá obsah, přeskakuji")
        return False
    
    # Pokud už má sumarizaci, přeskočíme
    if article.summary_simple:
        print(f"Článek {article.id} už má sumarizaci")
        return False
    
    print(f"Generuji sumarizaci pro článek {article.id}: {article.title}")
    
    try:
        # Jednoduchá sumarizace
        prompt_simple = f"""Summarize the following article in a few sentences - explain what happened.

If the content is prohibited or you cannot generate a summary, respond with: "Content unavailable for summarization."

Title: {article.title}

Content:
{article.content[:3000]}

Respond only with the summary, without any additional text."""
        
        response = llm.invoke(prompt_simple)
        article.summary_simple = response.content
        db.commit()
        print(f"  ✓ Sumarizace vygenerována")
        
        print(f"✓ Sumarizace pro článek {article.id} uložena")
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Přerušeno uživatelem")
        db.rollback()
        raise
    except Exception as e:
        print(f"✗ Chyba při generování sumarizace pro článek {article.id}: {e}")
        db.rollback()
        return False


def process_all_articles():
    """
    Projde všechny články v databázi a vygeneruje pro ně sumarizace.
    """
    db = SessionLocal()
    try:
        # Načteme všechny články
        articles = db.query(Article).all()
        print(f"Nalezeno {len(articles)} článků")
        
        processed = 0
        skipped = 0
        errors = 0
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}]")
            result = generate_summaries_for_article(article, db)
            if result:
                processed += 1
                # Pauza mezi články
                if i < len(articles):
                    time.sleep(DELAY_BETWEEN_ARTICLES)
            elif article.summary_simple:
                skipped += 1
            else:
                errors += 1
        
        print(f"\n=== Hotovo ===")
        print(f"Zpracováno: {processed}")
        print(f"Přeskočeno (už má sumarizaci): {skipped}")
        print(f"Chyby: {errors}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("Spouštím generování sumarizací...")
    process_all_articles()
