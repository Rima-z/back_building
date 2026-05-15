"""
Tests unitaires — IoT Connector Service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "iot-connector-service"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_connect_bad_credentials():
    """Doit retourner 401 si les credentials WaveOn sont invalides."""
    with patch("app.routers.iot_router.authenticate") as mock_auth:
        mock_auth.side_effect = Exception("Identifiants incorrects")
        response = client.post(
            "/api/iot/connect",
            json={"email": "wrong@test.com", "password": "bad"},
        )
    assert response.status_code == 401
    assert "Authentification WaveOn échouée" in response.json()["detail"]


def test_connect_success():
    """Doit retourner un session_id en cas de succès."""
    with patch("app.routers.iot_router.authenticate") as mock_auth:
        mock_auth.return_value = {
            "id_client": 1,
            "id_user": 42,
            "token": "fake_token",
            "database_ip": None,
            "database_port": None,
        }
        response = client.post(
            "/api/iot/connect",
            json={"email": "user@test.com", "password": "pass"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["id_client"] == 1


def test_sensors_invalid_session():
    """Doit retourner 404 pour une session inconnue."""
    response = client.get("/api/iot/sensors/session_inexistante")
    assert response.status_code == 404


def test_list_sessions_empty():
    response = client.get("/api/iot/sessions")
    assert response.status_code == 200
    assert "sessions" in response.json()


def test_connect_and_get_networks():
    """Test du flux complet : connexion + récupération réseaux (mocké)."""
    with patch("app.routers.iot_router.authenticate") as mock_auth, \
         patch("app.routers.iot_router.get_networks") as mock_nets:

        mock_auth.return_value = {
            "id_client": 1, "id_user": 10, "token": "tok", "database_ip": None, "database_port": None
        }
        mock_nets.return_value = [
            {"id_network": 2, "name": "Réseau Principal", "last_update": None}
        ]

        # Connexion
        r1 = client.post("/api/iot/connect", json={"email": "a@b.com", "password": "p"})
        assert r1.status_code == 200
        sid = r1.json()["session_id"]

        # Réseaux
        r2 = client.get(f"/api/iot/networks/{sid}")
        assert r2.status_code == 200
        assert r2.json()["total"] == 1
        assert r2.json()["networks"][0]["name"] == "Réseau Principal"
