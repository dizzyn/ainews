from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

import os
import sys
from dotenv import load_dotenv

# Tímto přidáme kořenový adresář do cesty, aby Python viděl "src"
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Načtení konfigurace Alembic
config = context.config

# Nastavení logování
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- ZMĚNA 1: Import našich modelů ---
from src.database import Base
from src.models import * # Import všech modelů

# Nastavení target_metadata pro autogenerate
target_metadata = Base.metadata

# --- ZMĚNA 2: Načtení URL z proměnné prostředí ---
# Toto zajistí, že Alembic použije DATABASE_URL z docker-compose/local env
load_dotenv()
database_url = os.getenv("DATABASE_URL")

if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Vytvoření connectable object
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()