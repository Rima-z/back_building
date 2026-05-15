"""
Tests unitaires — Mapping Service
Utilise SQLite en mémoire pour les tests (pas besoin de PostgreSQL)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db, Base

# Base SQLite en mémoire pour les tests
TEST_DATABASE_URL = "sqlite:///./test_mapping.db"

engine_test = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ──────────────────────────────────────────────
# Tests de base
# ──────────────────────────────────────────────

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "mapping-service"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_list_mappings_empty():
    response = client.get("/api/mapping/")
    assert response.status_code == 200
    assert response.json() == []


# ──────────────────────────────────────────────
# Tests CRUD complets
# ──────────────────────────────────────────────

SAMPLE_MAPPING = {
    "space_global_id": "TEST_GLOBAL_ID_001",
    "space_name": "Bureau Test 101",
    "space_long_name": "Bureau de test premier étage",
    "storey_name": "Niveau 1",
    "area_m2": 25.0,
    "project_name": "Projet Test",
    "sensors": [
        {
            "sensor_type": "ble_node",
            "unicast": "0x00A1",
            "device_name": "Capteur Temp 101",
            "network_id": 2,
            "sensor_types": ["Température", "Humidité"],
        }
    ],
}


def test_create_mapping():
    response = client.post("/api/mapping/", json=SAMPLE_MAPPING)
    assert response.status_code == 201
    data = response.json()
    assert data["space_global_id"] == "TEST_GLOBAL_ID_001"
    assert data["space_name"] == "Bureau Test 101"
    assert len(data["sensors"]) == 1
    assert data["sensors"][0]["unicast"] == "0x00A1"


def test_create_duplicate_mapping():
    """Doit retourner 409 si le space_global_id est déjà mappé."""
    response = client.post("/api/mapping/", json=SAMPLE_MAPPING)
    assert response.status_code == 409


def test_get_mapping_by_id():
    response = client.get("/api/mapping/1")
    assert response.status_code == 200
    assert response.json()["space_name"] == "Bureau Test 101"


def test_get_mapping_by_global_id():
    response = client.get("/api/mapping/space/TEST_GLOBAL_ID_001")
    assert response.status_code == 200
    assert response.json()["space_global_id"] == "TEST_GLOBAL_ID_001"


def test_get_mapping_not_found():
    response = client.get("/api/mapping/99999")
    assert response.status_code == 404


def test_update_mapping():
    response = client.put("/api/mapping/1", json={"notes": "Mise à jour test"})
    assert response.status_code == 200
    assert response.json()["notes"] == "Mise à jour test"


def test_add_sensor():
    response = client.post(
        "/api/mapping/1/sensors",
        json={
            "sensors": [
                {
                    "sensor_type": "smart_controller",
                    "unicast": "0x00B2",
                    "device_name": "Compteur Elec 101",
                    "network_id": 2,
                    "sensor_types": ["Comptage énergie/eau"],
                }
            ]
        },
    )
    assert response.status_code == 200
    assert len(response.json()["sensors"]) == 2


def test_export_json():
    response = client.get("/api/mapping/export/json")
    assert response.status_code == 200
    data = response.json()
    assert "mappings" in data
    assert data["total"] >= 1


def test_stats():
    response = client.get("/api/mapping/stats/summary")
    assert response.status_code == 200
    stats = response.json()
    assert "total_spaces" in stats
    assert stats["total_spaces"] >= 1


def test_bulk_import():
    response = client.post(
        "/api/mapping/bulk-import",
        json={
            "project_name": "Projet Bulk",
            "ifc_filename": "bulk_test.ifc",
            "mappings": [
                {
                    "space_global_id": "BULK_001",
                    "space_name": "Salle Bulk A",
                    "sensors": [
                        {
                            "sensor_type": "ble_node",
                            "unicast": "0x00C3",
                            "device_name": "Capteur Bulk A",
                            "network_id": 2,
                            "sensor_types": ["Présence/Occupation"],
                        }
                    ],
                },
                {
                    "space_global_id": "BULK_002",
                    "space_name": "Salle Bulk B",
                    "sensors": [],
                },
            ],
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["created"] == 2
    assert result["errors"] == []


def test_delete_mapping():
    response = client.delete("/api/mapping/1")
    assert response.status_code == 200
    # Vérifier que la salle est bien supprimée
    response2 = client.get("/api/mapping/1")
    assert response2.status_code == 404
