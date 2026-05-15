"""
Script d'initialisation de la base de données PostgreSQL.
À exécuter une seule fois avant le premier démarrage du service.

Usage :
    python init_db.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Vérification de la variable d'environnement
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ DATABASE_URL non définie. Copiez .env.example en .env et configurez-le.")
    sys.exit(1)

print(f"📦 Connexion à : {db_url.split('@')[-1]}")  # Masque les credentials

from app.db.database import engine, Base
from app.db.orm_models import SpaceMapping, SensorAssignment  # noqa: F401 — nécessaire pour enregistrer les modèles

print("🔧 Création des tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables créées avec succès :")
print("   - space_mappings")
print("   - sensor_assignments")
print()
print("🚀 Vous pouvez maintenant démarrer le service avec :")
print("   uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload")
