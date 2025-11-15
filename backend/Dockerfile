# backend/Dockerfile

# 1. Base image
FROM python:3.11-slim

# 2. Nastavení pracovního adresáře
WORKDIR /app

# 3. Instalace závislostí
# Kopírujeme jen requirements.txt, abychom využili Docker cache
# Nová instalace proběhne jen při změně requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kopírování kódu aplikace
COPY ./src ./src
COPY ./alembic ./alembic
COPY alembic.ini .

# 5. Vystavení portu
EXPOSE 8000

# 6. Výchozí příkaz
# Tento příkaz bude přepsán v docker-compose.yml,
# ale je dobré ho tu mít pro samostatné spuštění.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "src.main:app"]