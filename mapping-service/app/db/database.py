"""
Configuration SQLAlchemy — PostgreSQL 18
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# URL de connexion PostgreSQL
# Format : postgresql://user:password@host:port/dbname
# ──────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/digital_twin_mapping"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Vérifie la connexion avant chaque requête
    pool_size=10,
    max_overflow=20,
    echo=False,                # Passer à True pour voir les requêtes SQL en debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency FastAPI : fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
