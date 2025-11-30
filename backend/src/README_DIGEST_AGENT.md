# News Digest Agent

Agent pro generování personalizovaného přehledu zpráv.

## Popis

Agent prochází databázi článků, analyzuje jejich důležitost podle profilu uživatele a zpravodajských hodnot, a vytváří stručný přehled nejdůležitějších událostí.

## Funkce

1. **Načtení článků** - Přečte všechny souhrny z databáze
2. **Kategorizace** - Aplikuje profil uživatele a zpravodajské hodnoty, kategorizuje články jako:
   - Nezajímavé
   - Málo zajímavé
   - Velmi zajímavé
   - Nezbytné
3. **Výběr článků** - Vybere nejrelevantnější články pro přehled
4. **Generování přehledu** - Přečte původní texty a sestaví přehled 3-7 vět
5. **Uložení** - Uloží přehled do databáze (přepíše předchozí)

## Profil uživatele

- Uživatel je čech, žije v Praze
- Zajímá ho politika, technologie, ekonomie a veřejné dění
- Rád by měl přehled o tom, co hýbe společností

## Zpravodajské hodnoty

Agent aplikuje tyto zpravodajské hodnoty:
- Aktualita
- Blízkost (geografická/kulturní)
- Dopad
- Prominentnost
- Konflikt
- Neobvyklost
- Lidský zájem
- Relevance

## Použití

### Spuštění

```bash
cd backend/src
python news_digest_agent.py
```

### Požadavky

- Nastavené proměnné prostředí v `.env`:
  - `GOOGLE_API_KEY` - API klíč pro Gemini
  - `GEMINI_MODEL` - Model (výchozí: gemini-2.0-flash-lite)
  - `DATABASE_URL` - Připojení k databázi

### Výstup

Agent vytvoří/aktualizuje záznam v databázi s URL="DIGEST", který obsahuje:
- Stručný přehled (3-7 vět, ~1 minuta čtení)
- Přepsáno vlastními slovy
- Jednotný styl
- Zaměřeno na nejdůležitější události

## Architektura

- **Agent loop** - Hlavní proces v metodě `run()`
- **Nástroje**:
  - Čtení ze databáze (souhrny, obsah článků)
  - Zápis do databáze
  - LLM (Gemini) pro analýzu a generování
- **Správa kontextu** - Zpracování po dávkách (batch_size=20)
- **Console log** - Průběžný výpis s časovými značkami

## Technologie

- **LangChain** - Framework pro práci s LLM
- **Google Gemini** - LLM model pro analýzu a generování
- **SQLAlchemy** - ORM pro práci s databází
- **Pydantic** - Strukturované výstupy z LLM
