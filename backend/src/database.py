import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Načteme URL z proměnné prostředí (z .env -> docker-compose)
DATABASE_URL = os.getenv("DATABASE_URL")

# Vytvoření "engine" - hlavního připojovacího bodu
engine = create_engine(DATABASE_URL)

# Vytvoření "SessionLocal" - továrny na databázové session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Vytvoření "Base" - základní třídy pro všechny tvé ORM modely
Base = declarative_base()

# Funkce (dependency) pro FastAPI, která poskytne session pro každý request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()