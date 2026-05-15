"""
IFC Parser Service — Microservice 1
Endpoint principal pour upload et parsing de fichiers IFC
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.parser.routers import ifc_router
import uvicorn

app = FastAPI(
    title="IFC Parser Service",
    description="Microservice de parsing de fichiers IFC pour le Jumeau Numérique",
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

app.include_router(ifc_router.router, prefix="/api/ifc", tags=["IFC"])


@app.get("/", tags=["Health"])
def root():
    return {"service": "ifc-parser-service", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)