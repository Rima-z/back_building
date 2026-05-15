"""
Routes FastAPI pour le IoT Connector Service
"""

import uuid
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.waveon.client import (
    authenticate,
    get_networks,
    get_smart_controllers,
    get_ble_nodes,
)
from app.models.schemas import LoginRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache en mémoire des sessions authentifiées
# clé = session_id, valeur = { credentials + données récupérées }
_sessions: dict = {}


# ──────────────────────────────────────────────
# Authentification
# ──────────────────────────────────────────────

@router.post("/connect", summary="Authentification WaveOn")
def connect(body: LoginRequest):
    """
    Se connecte à la plateforme WaveOn avec email/password.
    Retourne un **session_id** à utiliser dans tous les appels suivants.
    """
    try:
        credentials = authenticate(body.email, body.password, body.device_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentification WaveOn échouée : {str(e)}",
        )

    session_id = uuid.uuid4().hex
    _sessions[session_id] = {
        "credentials": credentials,
        "networks": None,
        "smart_controllers": None,
        "ble_nodes": None,
    }

    return {
        "session_id": session_id,
        "id_client": credentials["id_client"],
        "id_user": credentials["id_user"],
        "message": "Connexion WaveOn réussie. Utilisez session_id pour les appels suivants.",
    }


# ──────────────────────────────────────────────
# Réseaux
# ──────────────────────────────────────────────

@router.get("/networks/{session_id}", summary="Récupère les réseaux WaveOn")
def list_networks(session_id: str):
    """
    Retourne la liste de tous les réseaux du compte WaveOn.
    """
    session = _get_session(session_id)
    creds = session["credentials"]

    try:
        networks = get_networks(
            creds["id_client"], creds["id_user"], creds["token"]
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur WaveOn : {str(e)}")

    session["networks"] = networks
    return {"session_id": session_id, "total": len(networks), "networks": networks}


# ──────────────────────────────────────────────
# SmartControllers (compteurs énergie / eau)
# ──────────────────────────────────────────────

@router.get("/controllers/{session_id}", summary="Récupère les SmartControllers")
def list_controllers(session_id: str):
    """
    Retourne tous les SmartControllers (compteurs énergie/eau) du compte.
    Les réseaux sont récupérés automatiquement si pas encore chargés.
    """
    session = _get_session(session_id)
    creds = session["credentials"]
    networks = _ensure_networks(session, creds)

    try:
        controllers = get_smart_controllers(
            creds["id_client"], creds["id_user"], creds["token"], networks
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur WaveOn : {str(e)}")

    session["smart_controllers"] = controllers
    return {
        "session_id": session_id,
        "total": len(controllers),
        "smart_controllers": controllers,
    }


# ──────────────────────────────────────────────
# Capteurs BLE Mesh
# ──────────────────────────────────────────────

@router.get("/sensors/{session_id}", summary="Récupère les capteurs BLE Mesh")
def list_sensors(session_id: str):
    """
    Retourne tous les capteurs BLE Mesh avec leur type (température,
    humidité, présence, luminosité, etc.).
    """
    session = _get_session(session_id)
    creds = session["credentials"]
    networks = _ensure_networks(session, creds)

    try:
        ble_nodes = get_ble_nodes(
            creds["id_client"], creds["id_user"], creds["token"], networks
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur WaveOn : {str(e)}")

    session["ble_nodes"] = ble_nodes
    return {
        "session_id": session_id,
        "total": len(ble_nodes),
        "sensors": ble_nodes,
    }


# ──────────────────────────────────────────────
# Vue consolidée (tous les équipements)
# ──────────────────────────────────────────────

@router.get("/devices/{session_id}", summary="Tous les équipements IoT consolidés")
def list_all_devices(session_id: str):
    """
    Retourne en un seul appel : réseaux + SmartControllers + capteurs BLE.
    Pratique pour alimenter l'interface de mapping.
    """
    session = _get_session(session_id)
    creds = session["credentials"]
    networks = _ensure_networks(session, creds)

    try:
        controllers = get_smart_controllers(
            creds["id_client"], creds["id_user"], creds["token"], networks
        )
        ble_nodes = get_ble_nodes(
            creds["id_client"], creds["id_user"], creds["token"], networks
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur WaveOn : {str(e)}")

    session["smart_controllers"] = controllers
    session["ble_nodes"] = ble_nodes

    return {
        "session_id": session_id,
        "networks": networks,
        "smart_controllers": controllers,
        "sensors": ble_nodes,
        "summary": {
            "networks": len(networks),
            "smart_controllers": len(controllers),
            "ble_sensors": len(ble_nodes),
            "total_devices": len(controllers) + len(ble_nodes),
        },
    }


# ──────────────────────────────────────────────
# Sessions
# ──────────────────────────────────────────────

@router.get("/sessions", summary="Liste des sessions actives")
def list_sessions():
    return {
        "sessions": [
            {
                "session_id": sid,
                "id_client": s["credentials"]["id_client"],
                "networks_loaded": s["networks"] is not None,
                "controllers_loaded": s["smart_controllers"] is not None,
                "sensors_loaded": s["ble_nodes"] is not None,
            }
            for sid, s in _sessions.items()
        ]
    }


@router.delete("/sessions/{session_id}", summary="Déconnecte une session")
def delete_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    del _sessions[session_id]
    return {"message": f"Session {session_id} supprimée."}


# ──────────────────────────────────────────────
# Helpers internes
# ──────────────────────────────────────────────

def _get_session(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' introuvable. Appelez d'abord POST /api/iot/connect.",
        )
    return session


def _ensure_networks(session: dict, creds: dict) -> list:
    """Charge les réseaux si pas encore en cache pour cette session."""
    if session["networks"] is None:
        try:
            session["networks"] = get_networks(
                creds["id_client"], creds["id_user"], creds["token"]
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Erreur chargement réseaux : {str(e)}")
    return session["networks"]
