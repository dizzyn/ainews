"""
Agent pro generování personalizovaného přehledu zpráv.

Agent prochází databázi článků, analyzuje jejich důležitost podle profilu uživatele
a zpravodajských hodnot, a vytváří stručný přehled nejdůležitějších událostí.
"""

import os
import json
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from .database import SessionLocal, engine
from .models import Article, Base

# Načteme .env
load_dotenv()

# Profil uživatele
USER_PROFILE = """
Uživatel je čech, žije v Praze.
Zajímá ho politika, technologie, ekonomie a veřejné dění.
Rád by měl přehled o tom, co hýbe společností.
"""

# Zpravodajské hodnoty (podle https://cs.wikipedia.org/wiki/Zpravodajsk%C3%A9_hodnoty)
NEWS_VALUES = """
Zpravodajské hodnoty:
1. Aktualita - čerstvost události
2. Blízkost - geografická nebo kulturní blízkost
3. Dopad - počet lidí, které událost ovlivňuje
4. Prominentnost - zapojení známých osobností
5. Konflikt - spory, konflikty, kontroverze
6. Neobvyklost - překvapivé, neočekávané události
7. Lidský zájem - emocionální příběhy
8. Relevance - důležitost pro společnost
"""


class ArticleRelevance(BaseModel):
    """Model pro hodnocení relevance článku."""
    article_id: int = Field(description="ID článku")
    relevance: str = Field(description="Kategorie: Nezajímavé, Málo zajímavé, Velmi zajímavé, Nezbytné")
    news_value_score: int = Field(description="Číselné skóre zpravodajské hodnoty 1-10")
    news_values: List[str] = Field(description="Seznam přítomných zpravodajských hodnot")
    reasoning: str = Field(description="Stručné zdůvodnění hodnocení")
    country: str = Field(description="Hlavní země zprávy (např. Česko, Rusko, USA)")
    person: str = Field(description="Hlavní osoba zprávy (pokud existuje, jinak prázdný řetězec)")
    topic: str = Field(description="Hlavní téma (politika, ekonomika, technologie, kultura, bezpečnost)")


class ArticleRelevanceList(BaseModel):
    """Seznam hodnocení článků."""
    articles: List[ArticleRelevance]


class NewsDigestAgent:
    """Agent pro generování personalizovaného přehledu zpráv."""
    
    def __init__(self):
        """Inicializace agenta."""
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3
        )
        self.db: Session = SessionLocal()
        self.log("Agent inicializován")
    
    def log(self, message: str, verbose: bool = False):
        """Výpis do konzole s časovou značkou."""
        if verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
        else:
            print(message)
    
    def close(self):
        """Uzavření databázového spojení."""
        self.db.close()
    
    def fetch_articles_with_summaries(self) -> List[Article]:
        """Načte všechny články se souhrny z databáze."""
        articles = self.db.query(Article).filter(
            Article.summary_simple.isnot(None)
        ).all()
        self.log(f"📰 Načteno {len(articles)} článků")
        return articles

    
    def categorize_articles(self, articles: List[Article]) -> List[ArticleRelevance]:
        """
        Kategorizuje články podle profilu uživatele a zpravodajských hodnot.
        
        Args:
            articles: Seznam článků k hodnocení
            
        Returns:
            Seznam hodnocení relevance článků
        """
        self.log(f"🔍 Kategorizuji {len(articles)} článků...")
        
        # Připravíme data pro LLM - pouze souhrny
        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "summary": article.summary_simple,
                "published_date": article.published_date.isoformat() if article.published_date else None
            })
        
        # Zpracování po dávkách (kvůli limitu kontextu)
        batch_size = 20
        all_relevances = []
        
        for i in range(0, len(articles_data), batch_size):
            batch = articles_data[i:i + batch_size]
            
            prompt = f"""You are an expert in news analysis. Your task is to evaluate the relevance of articles according to user profile and news values.

{USER_PROFILE}

{NEWS_VALUES}

For each article determine:
1. Relevance category: Nezajímavé, Málo zajímavé, Velmi zajímavé, Nezbytné
2. News value score: 1-10 (overall importance score)
3. Which news values are present
4. Main country (e.g., Česko, Rusko, USA, Německo)
5. Main person (if any, otherwise empty string)
6. Main topic (politika, ekonomika, technologie, kultura, bezpečnost)
7. Brief reasoning in Czech

Respond in JSON array format with objects:
{{
  "article_id": <id>,
  "relevance": "<kategorie>",
  "news_value_score": <1-10>,
  "news_values": ["hodnota1", "hodnota2"],
  "country": "<země>",
  "person": "<osoba nebo prázdný řetězec>",
  "topic": "<téma>",
  "reasoning": "<zdůvodnění v češtině>"
}}

Articles to evaluate:
{json.dumps(batch, ensure_ascii=False, indent=2)}

Respond only with JSON array, no additional text."""
            
            response = self.llm.invoke(prompt)
            
            # Parsování JSON odpovědi
            try:
                response_text = response.content.strip()
                # Odstranění markdown code blocku pokud existuje
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                batch_results = json.loads(response_text)
                for item in batch_results:
                    all_relevances.append(ArticleRelevance(
                        article_id=item["article_id"],
                        relevance=item["relevance"],
                        news_value_score=item.get("news_value_score", 5),
                        news_values=item["news_values"],
                        country=item.get("country", ""),
                        person=item.get("person", ""),
                        topic=item.get("topic", ""),
                        reasoning=item["reasoning"]
                    ))
            except Exception as e:
                self.log(f"❌ Chyba při parsování: {e}")
                continue
        
        self.log(f"✅ Kategorizováno {len(all_relevances)} článků")
        return all_relevances
    
    def select_articles_for_digest(self, relevances: List[ArticleRelevance], articles: List[Article]) -> Tuple[List[ArticleRelevance], Dict]:
        """
        Vybere a seřadí články pro finální přehled.
        
        Args:
            relevances: Seznam hodnocení článků
            articles: Seznam článků z databáze
            
        Returns:
            Tuple (seřazené relevance, mapa článků podle ID)
        """
        # Prioritizace: Nezbytné > Velmi zajímavé > Málo zajímavé
        priority_map = {
            "Nezbytné": 4,
            "Velmi zajímavé": 3,
            "Málo zajímavé": 2,
            "Nezajímavé": 1
        }
        
        # Vybereme top články (minimálně Velmi zajímavé)
        selected_relevances = [
            rel for rel in relevances 
            if rel.relevance in ["Nezbytné", "Velmi zajímavé"]
        ][:15]
        
        # Pokud je málo článků, přidáme i "Málo zajímavé"
        if len(selected_relevances) < 5:
            more = [rel for rel in relevances if rel.relevance == "Málo zajímavé"][:10]
            selected_relevances.extend(more)
        
        # Seřadíme podle news_value_score
        selected_relevances.sort(key=lambda x: x.news_value_score, reverse=True)
        
        # Vytvoříme mapu článků
        articles_map = {a.id: a for a in articles}
        
        # Výpis seřazených zpráv
        self.log(f"\n📊 Seřazené zprávy podle hodnoty:")
        for rel in selected_relevances:
            article = articles_map.get(rel.article_id)
            if article:
                title_short = article.title[:60] + "..." if len(article.title) > 60 else article.title
                self.log(f"  [{rel.news_value_score}/10] {rel.relevance[:4]}. | {rel.country:8} | {title_short}")
        
        self.log(f"\n✅ Vybráno {len(selected_relevances)} článků\n")
        return selected_relevances, articles_map
    
    def generate_digest(self, selected_relevances: List[ArticleRelevance], articles_map: Dict) -> str:
        """
        Vygeneruje finální přehled zpráv z vybraných článků.
        
        Args:
            selected_relevances: Seřazené hodnocení článků
            articles_map: Mapa článků podle ID
            
        Returns:
            Textový přehled zpráv
        """
        self.log(f"✍️  Generuji přehled...")
        
        # Připravíme data pro LLM s metadaty pro lepší spojování
        articles_content = []
        for rel in selected_relevances:
            article = articles_map.get(rel.article_id)
            if article:
                articles_content.append({
                    "title": article.title,
                    "summary": article.summary_simple,
                    "country": rel.country,
                    "person": rel.person,
                    "topic": rel.topic,
                    "score": rel.news_value_score
                })
        
        # Prompt pro generování přehledu
        prompt = f"""Jsi zkušený novinář. Tvým úkolem je napsat stručný přehled nejdůležitějších zpráv.

{USER_PROFILE}

KRITICKÁ PRAVIDLA SPOJOVÁNÍ:
Priority pro spojování zpráv do jedné věty:
1. NEJVYŠŠÍ: Týkají se stejné osoby (person)
2. VYSOKÁ: Týkají se stejné země (kromě "Česko" - české zprávy nespojuj)
3. STŘEDNÍ: Mají podobný nebo opačný dopad
4. NÍZKÁ: Jsou ze stejného tématu (topic)

STRUKTURA:
- Délka: 6-8 vět (max 600 znaků)
- Začni hodnotícím komentářem, pak vyjmenuj zprávy jako argumenty
- Příklad: "Rusko pokračuje v represi - perzekuce intelektuálů se stupňuje a Červený kříž spolupracuje s Kremlem."
- Řaď zprávy podle score (nejvyšší první)

STYL:
- Kratší fráze: "stalo se" místo "došlo k", "v" místo "v oblasti"
- Plynulý text, ne seznam
- Tón: rychlý, výstižný, čtivý

Články k zpracování (seřazené podle důležitosti):
{json.dumps(articles_content, ensure_ascii=False, indent=2)}

Napiš přehled v češtině:"""
        
        response = self.llm.invoke(prompt)
        digest_text = response.content
        
        self.log(f"✅ Přehled vygenerován ({len(digest_text)} znaků)")
        return digest_text

    
    def save_digest(self, digest_text: str):
        """
        Uloží přehled do databáze (přepíše předchozí).
        
        Args:
            digest_text: Text přehledu k uložení
        """
        # Vytvoříme nebo aktualizujeme záznam
        # Použijeme speciální článek s ID=0 nebo URL="DIGEST"
        digest_article = self.db.query(Article).filter(Article.url == "DIGEST").first()
        
        if digest_article:
            # Aktualizujeme existující
            digest_article.title = f"Přehled zpráv - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            digest_article.content = digest_text
            digest_article.summary_simple = digest_text
            digest_article.published_date = datetime.now()
        else:
            # Vytvoříme nový
            digest_article = Article(
                url="DIGEST",
                title=f"Přehled zpráv - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=digest_text,
                summary_simple=digest_text,
                published_date=datetime.now()
            )
            self.db.add(digest_article)
        
        self.db.commit()
        self.log(f"💾 Uloženo do DB")
    
    def run(self):
        """Hlavní loop agenta - spustí celý proces generování přehledu."""
        try:
            self.log("🚀 START: Generování přehledu zpráv")
            
            # 1. Načteme články se souhrny
            articles = self.fetch_articles_with_summaries()
            
            if not articles:
                self.log("⚠️  Žádné články k zpracování")
                return
            
            # 2. Kategorizujeme články
            relevances = self.categorize_articles(articles)
            
            # 3. Vybereme a seřadíme články pro přehled
            selected_relevances, articles_map = self.select_articles_for_digest(relevances, articles)
            
            if not selected_relevances:
                self.log("⚠️  Žádné relevantní články")
                return
            
            # 4. Vygenerujeme přehled
            digest = self.generate_digest(selected_relevances, articles_map)
            
            # 5. Uložíme do databáze
            self.save_digest(digest)
            
            self.log(f"\n{'='*60}")
            self.log(f"📰 VÝSLEDNÝ PŘEHLED:")
            self.log(f"{'='*60}")
            self.log(digest)
            self.log(f"{'='*60}\n")
            self.log("✅ HOTOVO")
            
        except Exception as e:
            self.log(f"❌ CHYBA: {str(e)}")
            raise
        finally:
            self.close()


def main():
    """Hlavní funkce pro spuštění agenta."""
    agent = NewsDigestAgent()
    agent.run()


if __name__ == "__main__":
    main()
