# News Digest

Automatický systém pro sběr, analýzu a sumarizaci zpráv pomocí AI.

## Spuštění

```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Production
docker-compose up -d --build
```

## Workflow

### 1. Crawler - Sběr zpráv
```bash
docker-compose -f docker-compose.dev.yml exec backend python -m src.crawler
```

### 2. Content Crawler - Stažení obsahu článků
```bash
docker-compose -f docker-compose.dev.yml exec backend python -m src.content_crawler
```

### 3. Generate Summary - Vytvoření souhrnů
```bash
docker-compose -f docker-compose.dev.yml exec backend python -m src.generate_summary
```

### 4. News Digest Agent - Finální přehled
```bash
docker-compose -f docker-compose.dev.yml exec backend python -m src.news_digest_agent
```

## Frontend

- **Aplikace**: http://localhost:5173/
- **API Docs**: http://localhost:8000/docs

## Databáze

```bash
# Migrace
docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "Popis změny"
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

## Research plan
- [x] Crawlers - We have articles
- [x] Summary - LLM sumarise the articles
- [x] RAG - we can search the summaries
- [x] News products

  - [x] # News digest
    - [x] Agentic
    - [x] Soriting the news by News values
    - [x] Over-all summary

  - [ ] # Developing Story
    - [ ] Agentic
    - [ ] Find all relevant news
    - [ ] Over-all summary