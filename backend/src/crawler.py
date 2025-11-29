import asyncio
import os
import json
from typing import List, Optional
from dotenv import load_dotenv

from playwright.async_api import async_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from .database import SessionLocal
from .models import Article as DBArticle

# 1. Načtení API klíče a konfigurace
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL", "https://www.novinky.cz")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "100"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "20"))

# 2. Definice datových modelů (Vstup a Výstup pro AI)
class LinkItem(BaseModel):
    text: str
    url: str

    # Pěkný výpis pro debugování
    def __repr__(self):
        return f"[{self.text[:20]}...] -> {self.url}"

class ArticleItem(BaseModel):
    """
    Jedna vybraná zpráva s kategorizací.
    """
    index: int = Field(
        description="Index zprávy ze vstupního seznamu (0-based)",
        ge=0
    )
    what_happened: str = Field(
        description="V krátké větě: co se stalo, co dříve nebylo a teď je, jaká nová informace byla zjištěna.",
        min_length=10,
        max_length=500
    )
    impact_on: str = Field(
        description="Na koho má událost dopad - jednotlivec, skupina, organizace, stát, atd.",
        min_length=5,
        max_length=300
    )
    countries: List[str] = Field(
        default_factory=list,
        description="Seznam zemí, kterých se zpráva týká (např. Česko, Německo, USA, EU). Prázdný seznam pokud se netýká konkrétní země.",
        max_length=10
    )
    people: List[str] = Field(
        default_factory=list,
        description="Seznam veřejných osob (jméno nebo funkce), kterých se zpráva týká. Prázdný seznam pokud se netýká konkrétní osoby.",
        max_length=20
    )

class ArticleSelection(BaseModel):
    """
    Toto je struktura, kterou chceme, aby nám AI vrátila.
    LangChain zajistí, že dostaneme přesně tento formát (JSON).
    """
    articles: List[ArticleItem] = Field(
        description="Seznam vybraných zpráv s jejich indexy a kategorizací."
    )

# 3. Nastavení AI (Gemini 1.5 Flash)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0,
)

# Připojíme schéma výstupu k modelu
ai_selector = llm.with_structured_output(ArticleSelection)

async def get_page_links(url: str) -> List[LinkItem]:
    """
    Pomocí Playwright stáhne odkazy, vyčistí je a odstraní duplicity.
    """
    async with async_playwright() as p:
        print(f"🌍 Načítám stránku: {url}")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            
            # JavaScript v prohlížeči pro rychlou extrakci
            raw_data = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map(a => ({
                    text: a.innerText.replace(/[\\n\\t]/g, ' ').trim(), // Odstranění odřádkování
                    url: a.href
                }));
            }""")
            
        finally:
            await browser.close()

    print(f"🔎 Nalezeno surových odkazů: {len(raw_data)}")

    # --- Python Filtrace (Cleaning) ---
    unique_map = {}
    
    for item in raw_data:
        text = item['text']
        url = item['url']
        
        # 1. Musí to být http(s) odkaz
        if not url.startswith("http"):
            continue
            
        # 2. Musí mít text (netextové odkazy zahazujeme)
        #    Ignorujeme i velmi krátké texty (čísla stránek, "více", atd.)
        if not text or len(text) < 5:
            continue
            
        # 3. Dedupikace (podle URL)
        # Pokud už URL máme, ale tenhle nový odkaz má delší text (lepší kontext), přepíšeme ho
        if url not in unique_map:
            unique_map[url] = LinkItem(text=text, url=url)
        else:
            if len(text) > len(unique_map[url].text):
                unique_map[url] = LinkItem(text=text, url=url)

    clean_links = list(unique_map.values())
    print(f"🧹 Po vyčištění a deduplikaci zbývá: {len(clean_links)} odkazů.")
    return clean_links


async def analyze_chunk_with_ai(links: List[LinkItem], chunk_offset: int = 0) -> List[ArticleItem]:
    """
    Pošle jeden chunk odkazů do Gemini k posouzení.
    Vrátí seznam článků s indexy a kategorizací.
    chunk_offset se přičítá k indexům pro správné mapování na celkový seznam.
    """
    if not links:
        return []
    
    print(f"🤖 Analyzuji chunk {chunk_offset}-{chunk_offset + len(links) - 1}...")
    
    # Vytvoříme indexovaný seznam nadpisů (s lokálními indexy)
    indexed_titles = "\n".join([f"{i}. {link.text}" for i, link in enumerate(links)])
    
    prompt_text = (
        "You are an editorial robot. Your task is to review an indexed list of headlines from a news website's main page "
        "and select ONLY those that are **news with informational value**.\n\n"
        "CRITERIA FOR SELECTING NEWS:\n"
        "A news item must meet BOTH of the following criteria:\n"
        "1. Something NEW happened or we learned something that was not previously known\n"
        "2. The reported event has an IMPACT on someone (individual, group, organization, state)\n\n"
        "WHAT TO EXCLUDE:\n"
        "- Navigation links (Home, Sports, Weather, Authors, Archive)\n"
        "- Footer, advertisements, login, and technical pages\n"
        "- General articles without a specific event (tips, guides, product reviews)\n"
        "- Comments and analyses without a new event (look for prefixes like 'komentář', 'point of view', or similar)\n"
        "- Sports results and entertainment news (unless they have broader social impact)\n"
        "- Jokes and artistic content (in Czech: 'vtip', 'umění') - these may look like articles but are entertainment/art content\n"
        "- Opinion pieces and commentaries - some commentators write their findings but it's not news (recognizable by 'komentář', 'point of view', or similar prefixes)\n\n"
        "FOR EACH SELECTED NEWS ITEM, DETERMINE:\n"
        "1. **what_happened**: In a short sentence, summarize what happened - what was not there before and is now\n"
        "2. **impact_on**: Who is affected by the event (e.g., 'citizens of Czech Republic', 'employees of company X', 'patients', 'Donald Trump')\n"
        "3. **countries**: List of countries the news relates to (Czech Republic, Germany, USA, EU, etc.)\n"
        "4. **people**: List of public figures (name or position) the news relates to\n\n"
        "Return the indices of selected news items (0-based) along with complete categorization.\n\n"
        f"List of headlines:\n{indexed_titles}"
    )
    
    try:
        result = await ai_selector.ainvoke(prompt_text)
        # Přičteme offset k indexům pro správné mapování
        for article in result.articles:
            article.index += chunk_offset
        return result.articles
    except Exception as e:
        print(f"❌ Chyba při komunikaci s AI: {e}")
        return []


async def analyze_with_ai_in_chunks(links: List[LinkItem], chunk_size: int = CHUNK_SIZE) -> List[ArticleItem]:
    """
    Rozdělí odkazy na menší chunky a zpracuje je postupně.
    Vrátí agregovaný seznam všech vybraných článků.
    """
    if not links:
        return []
    
    all_articles = []
    total_chunks = (len(links) + chunk_size - 1) // chunk_size
    
    print(f"\n📦 Zpracovávám {len(links)} odkazů v {total_chunks} chuncích po {chunk_size}...")
    
    for i in range(0, len(links), chunk_size):
        chunk = links[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        print(f"\n--- Chunk {chunk_num}/{total_chunks} ---")
        
        articles = await analyze_chunk_with_ai(chunk, chunk_offset=i)
        all_articles.extend(articles)
        
        print(f"   ✓ Nalezeno {len(articles)} zpráv v tomto chunku")
    
    print(f"\n✅ Celkem nalezeno {len(all_articles)} zpráv ze všech chunků")
    return all_articles


def save_to_database(articles: List[ArticleItem], links: List[LinkItem]) -> None:
    """
    Smaže databázi a uloží nové zprávy.
    """
    db = SessionLocal()
    try:
        # 1. Smazání všech existujících článků
        print("\n🗑️  Mažu staré zprávy z databáze...")
        deleted_count = db.query(DBArticle).delete()
        print(f"   Smazáno: {deleted_count} zpráv")
        
        # 2. Uložení nových zpráv
        print("\n💾 Ukládám nové zprávy do databáze...")
        for article in articles:
            if 0 <= article.index < len(links):
                link = links[article.index]
                
                # Vytvoření kategorizace jako JSON string
                categories_data = {
                    "what_happened": article.what_happened,
                    "impact_on": article.impact_on,
                    "countries": article.countries,
                    "people": article.people
                }
                
                db_article = DBArticle(
                    title=link.text,
                    url=link.url,
                    categories=json.dumps(categories_data, ensure_ascii=False)
                )
                db.add(db_article)
        
        db.commit()
        print(f"   ✅ Uloženo: {len(articles)} zpráv")
        
    except Exception as e:
        db.rollback()
        print(f"   ❌ Chyba při ukládání do databáze: {e}")
        raise
    finally:
        db.close()


async def main():
    # 1. Krok: Získání dat
    links = await get_page_links(TARGET_URL)
    
    # 2. Krok: Příprava kandidátů
    # Seřadíme podle délky textu sestupně (články mívají dlouhé titulky)
    # a vezmeme prvních MAX_ARTICLES kandidátů
    sorted_links = sorted(links, key=lambda x: len(x.text), reverse=True)
    top_candidates = sorted_links[:MAX_ARTICLES]
    
    print(f"\n📊 Zpracovávám {len(top_candidates)} kandidátů (MAX_ARTICLES={MAX_ARTICLES})")
    
    # 3. Krok: Analýza AI po chuncích
    articles = await analyze_with_ai_in_chunks(top_candidates, chunk_size=CHUNK_SIZE)

    # 4. Krok: Uložení do databáze
    save_to_database(articles, top_candidates)

    # 5. Krok: Výpis
    print("\n" + "="*60)
    print(f"✅ VÝSLEDEK: Nalezeno {len(articles)} zpráv")
    print("="*60)
    
    for i, article in enumerate(articles, 1):
        # Rekonstrukce nadpisu podle indexu
        if 0 <= article.index < len(top_candidates):
            title = top_candidates[article.index].text
        else:
            title = "⚠️ Neplatný index"
        
        print(f"\n{i:02d}. {title}")
        
        # Výpis nových klasifikací
        print(f"    📰 Co se stalo: {article.what_happened}")
        print(f"    🎯 Dopad na: {article.impact_on}")
        
        # Výpis původních kategorií
        if article.countries:
            print(f"    🌍 Země: {', '.join(article.countries)}")
        if article.people:
            print(f"    👤 Osoby: {', '.join(article.people)}")

if __name__ == "__main__":
    asyncio.run(main())