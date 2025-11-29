import asyncio
from datetime import datetime
from typing import Optional
import trafilatura
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Article as DBArticle


def fetch_article_content(url: str) -> tuple[Optional[str], Optional[datetime]]:
    """
    Stáhne a rozparsuje článek pomocí Trafilatura.
    Vrací tuple (markdown_content, published_date).
    """
    try:
        print(f"📰 Stahuji článek: {url}")
        
        # Stažení HTML
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"   ❌ Nepodařilo se stáhnout URL")
            return None, None
        
        # Extrakce obsahu s metadaty
        metadata = trafilatura.extract_metadata(downloaded)
        content = trafilatura.extract(
            downloaded,
            output_format='markdown',
            include_comments=False,
            include_tables=True
        )
        
        if not content or len(content.strip()) < 100:
            print(f"   ⚠️ Příliš málo obsahu ({len(content) if content else 0} znaků)")
            return None, None
        
        # Získání data vydání z metadat
        published_date = None
        if metadata and metadata.date:
            try:
                published_date = datetime.fromisoformat(metadata.date)
            except:
                pass
        
        print(f"   ✓ Staženo {len(content)} znaků")
        return content, published_date
        
    except Exception as e:
        print(f"   ❌ Chyba při stahování článku {url}: {e}")
        return None, None


def process_articles(db: Session) -> dict:
    """
    Projde všechny články v databázi a doplní jejich obsah.
    Pokud článek už obsah má, přepíše ho.
    """
    articles = db.query(DBArticle).all()
    
    stats = {
        "total": len(articles),
        "success": 0,
        "failed": 0,
        "skipped": 0
    }
    
    print(f"\n🔄 Zpracovávám {stats['total']} článků...")
    
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{stats['total']}] {article.title[:60]}...")
        
        # Fetch obsahu
        content, published_date = fetch_article_content(article.url)
        
        if content:
            # Uložení do databáze (přepíše existující obsah)
            article.content = content
            article.published_date = published_date
            stats["success"] += 1
        else:
            stats["failed"] += 1
        
        # Commit po každém článku (aby se neztratila data při pádu)
        try:
            db.commit()
        except Exception as e:
            print(f"   ❌ Chyba při ukládání: {e}")
            db.rollback()
            stats["failed"] += 1
            stats["success"] -= 1
    
    return stats


async def main():
    """
    Hlavní funkce content crawleru.
    """
    print("="*60)
    print("🚀 Content Crawler Worker")
    print("="*60)
    
    db = SessionLocal()
    try:
        stats = process_articles(db)
        
        print("\n" + "="*60)
        print("✅ VÝSLEDEK")
        print("="*60)
        print(f"Celkem článků: {stats['total']}")
        print(f"Úspěšně staženo: {stats['success']}")
        print(f"Selhalo: {stats['failed']}")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
