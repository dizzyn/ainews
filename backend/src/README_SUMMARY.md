# Generate Summary Worker

Worker pro generování sumarizací článků pomocí Google Gemini.

## Co dělá

Projde všechny články v databázi a vygeneruje pro každý tři typy sumarizací:
- **Jednoduchá sumarizace** - shrnutí článku do několika vět
- **Vtipná sumarizace** - vtipný komentář k článku
- **Storytelling** - převyprávění článku jako příběh

## Použití

### Lokálně (s virtuálním prostředím)

```bash
cd backend
source ../.venv/bin/activate  # nebo .venv\Scripts\activate na Windows
python -m src.generate_summary
```

### V Dockeru

```bash
docker-compose -f docker-compose.dev.yml exec backend python -m src.generate_summary
```

## Poznámky

- Worker automaticky přeskakuje články, které už mají všechny sumarizace
- Každý článek se zpracuje pouze jednou (pokud už má sumarizace, přeskočí se)
- Vyžaduje GOOGLE_API_KEY v .env souboru
