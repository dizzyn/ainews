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

# 1. Načtení API klíče
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL", "https://www.novinky.cz")

# 2. Definice datových modelů (Vstup a Výstup pro AI)
class LinkItem(BaseModel):
    text: str
    url: str

    # Pěkný výpis pro debugování
    def __repr__(self):
        return f"[{self.text[:20]}...] -> {self.url}"

class ArticleItem(BaseModel):
    """
    Jeden vybraný článek s kategorizací.
    """
    index: int = Field(description="Index článku ze vstupního seznamu (0-based)")
    countries: List[str] = Field(
        description="Seznam zemí, kterých se článek týká (např. Česko, Německo, USA, EU). Prázdný seznam pokud se netýká konkrétní země."
    )
    people: List[str] = Field(
        description="Seznam veřejných osob (jméno nebo funkce), kterých se článek týká. Prázdný seznam pokud se netýká konkrétní osoby."
    )

class ArticleSelection(BaseModel):
    """
    Toto je struktura, kterou chceme, aby nám AI vrátila.
    LangChain zajistí, že dostaneme přesně tento formát (JSON).
    """
    articles: List[ArticleItem] = Field(
        description="Seznam vybraných článků s jejich indexy a kategorizací."
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


async def analyze_with_ai(links: List[LinkItem]) -> List[ArticleItem]:
    """
    Pošle seznam odkazů do Gemini k posouzení.
    Vrátí seznam článků s indexy a kategorizací.
    """
    if not links:
        return []
    
    print("🤖 Posílám data agentovi k analýze...")
    
    # Prompt (Instrukce pro agenta)
    # Vytvoříme indexovaný seznam nadpisů
    indexed_titles = "\n".join([f"{i}. {link.text}" for i, link in enumerate(links)])
    
    prompt_text = (
        "Jsi redakční robot. Tvým úkolem je projít indexovaný seznam nadpisů z hlavní stránky zpravodajského webu "
        "a vybrat POUZE ty, které jsou **konkrétní články** (zprávy, reportáže, komentáře).\n\n"
        "PRAVIDLA:\n"
        "1. VYBER nadpisy, které vypadají jako titulky článků.\n"
        "2. IGNORUJ navigační odkazy (Domů, Sport, Počasí, Autoři, Archiv).\n"
        "3. IGNORUJ patičku, reklamu, login a technické stránky.\n"
        "4. Pro každý vybraný článek urči:\n"
        "   - **země**: které se článek týká (Česko, Německo, USA, EU, atd.). Pokud se týká EU jako celku, uveď 'EU'.\n"
        "   - **osoby**: veřejné osoby (jméno nebo funkce), kterých se článek týká.\n\n"
        "Vrať indexy vybraných článků (0-based) spolu s kategorizací.\n\n"
        f"Seznam nadpisů:\n{indexed_titles}"
    )

    # print(prompt_text)
    
    try:
        result = await ai_selector.ainvoke(prompt_text)
        return result.articles
    except Exception as e:
        print(f"❌ Chyba při komunikaci s AI: {e}")
        return []


def save_to_database(articles: List[ArticleItem], links: List[LinkItem]) -> None:
    """
    Smaže databázi a uloží nové články.
    """
    db = SessionLocal()
    try:
        # 1. Smazání všech existujících článků
        print("\n🗑️  Mažu staré články z databáze...")
        deleted_count = db.query(DBArticle).delete()
        print(f"   Smazáno: {deleted_count} článků")
        
        # 2. Uložení nových článků
        print("\n💾 Ukládám nové články do databáze...")
        for article in articles:
            if 0 <= article.index < len(links):
                link = links[article.index]
                
                # Vytvoření kategorizace jako JSON string
                categories_data = {
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
        print(f"   ✅ Uloženo: {len(articles)} článků")
        
    except Exception as e:
        db.rollback()
        print(f"   ❌ Chyba při ukládání do databáze: {e}")
        raise
    finally:
        db.close()


async def main():
    # 1. Krok: Získání dat
    links = await get_page_links(TARGET_URL)
    
    # 2. Krok: Analýza AI
    # Pro jistotu vezmeme prvních 50 nejdelších odkazů (články mívají dlouhé titulky),
    # abychom neplatili za analýzu menu a patiček zbytečně.
    # (Seřadíme podle délky textu sestupně)
    sorted_links = sorted(links, key=lambda x: len(x.text), reverse=True)
    top_candidates = sorted_links[:50]
    
    articles = await analyze_with_ai(top_candidates)

    # 3. Krok: Uložení do databáze
    save_to_database(articles, top_candidates)

    # 4. Krok: Výpis
    print("\n" + "="*60)
    print(f"✅ VÝSLEDEK: Nalezeno {len(articles)} článků")
    print("="*60)
    
    for i, article in enumerate(articles, 1):
        # Rekonstrukce nadpisu podle indexu
        if 0 <= article.index < len(top_candidates):
            title = top_candidates[article.index].text
        else:
            title = "⚠️ Neplatný index"
        
        print(f"\n{i:02d}. {title}")
        
        # Výpis kategorií
        if article.countries:
            print(f"    🌍 Země: {', '.join(article.countries)}")
        if article.people:
            print(f"    👤 Osoby: {', '.join(article.people)}")

if __name__ == "__main__":
    asyncio.run(main())