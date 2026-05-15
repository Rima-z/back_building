"""
IoT Connector Service — Microservice 2
Connexion à l'API WaveOn IoT : authentification, réseaux, capteurs BLE, SmartControllers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import iot_router
import uvicorn

app = FastAPI(
    title="IoT Connector Service",
    description="Microservice de connexion à la plateforme WaveOn IoT pour le Jumeau Numérique",
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

app.include_router(iot_router.router, prefix="/api/iot", tags=["IoT WaveOn"])


@app.get("/", tags=["Health"])
def root():
    return {"service": "iot-connector-service", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
