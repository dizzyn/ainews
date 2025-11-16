
# Jak to spustit
- Dev: `docker-compose -f docker-compose.dev.yml up --build`
- Produkce: `docker-compose -f docker-compose.yml up -d --build`

# Migrace databaze
- `docker compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "Init: Vytvoření tabulky Article"`

# Generujeme typy z API
- `docker compose -f docker-compose.dev.yml exec frontend npm run gen-api`

# Linky
- http://localhost:5173/
- http://localhost:8000/docs
- http://localhost:8000/redoc
- http://localhost:8000/openapi.json