"""
Mapping Service — Microservice 3
Gère le mapping Salle IFC ↔ Capteurs WaveOn avec persistance PostgreSQL
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.routers import mapping_router
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création des tables au démarrage
Base.metadata.create_all(bind=engine)
logger.info("Tables PostgreSQL initialisées.")

app = FastAPI(
    title="Mapping Service",
    description="Microservice de mapping Salle IFC ↔ Capteurs WaveOn pour le Jumeau Numérique",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mapping_router.router, prefix="/api/mapping", tags=["Mapping"])


@app.get("/", tags=["Health"])
def root():
    return {"service": "mapping-service", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
