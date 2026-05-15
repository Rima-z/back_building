"""
Schémas Pydantic pour les requêtes / réponses du Mapping Service
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ──────────────────────────────────────────────
# Capteur (entrée)
# ──────────────────────────────────────────────

class SensorIn(BaseModel):
    sensor_type: str = Field(..., description="'ble_node' ou 'smart_controller'")
    device_id: Optional[str] = Field(None, description="ID WaveOn du capteur")
    unicast: Optional[str] = Field(None, description="Adresse unicast")
    device_name: Optional[str] = Field(None, description="Nom du capteur")
    network_id: Optional[int] = Field(None, description="ID réseau WaveOn")
    pid_label: Optional[str] = Field(None, description="Type fonctionnel")
    sensor_types: Optional[List[str]] = Field(default=[], description="Types de mesure")
    notes: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "sensor_type": "ble_node",
                "device_id": "42",
                "unicast": "0x00A1",
                "device_name": "Capteur Temp Bureau 201",
                "network_id": 2,
                "pid_label": "Interrupteur/Capteur/Dimmer",
                "sensor_types": ["Température", "Humidité"],
            }
        }
    }


# ──────────────────────────────────────────────
# Capteur (sortie)
# ──────────────────────────────────────────────

class SensorOut(SensorIn):
    id: int
    space_mapping_id: int
    assigned_at: Optional[datetime] = None
    is_active: bool


# ──────────────────────────────────────────────
# Mapping salle (entrée — création)
# ──────────────────────────────────────────────

class MappingCreate(BaseModel):
    space_global_id: str = Field(..., description="GlobalId IFC de la salle")
    space_name: str = Field(..., description="Nom IFC de la salle")
    space_long_name: Optional[str] = None
    storey_name: Optional[str] = None
    area_m2: Optional[float] = None
    project_name: Optional[str] = None
    ifc_filename: Optional[str] = None
    notes: Optional[str] = None
    sensors: List[SensorIn] = Field(default=[], description="Capteurs à associer à cette salle")

    model_config = {
        "json_schema_extra": {
            "example": {
                "space_global_id": "2BuScNrX9BOfc20VVyh05w",
                "space_name": "Bureau 201",
                "space_long_name": "Bureau direction 2e étage",
                "storey_name": "Niveau 2",
                "area_m2": 32.5,
                "project_name": "Bâtiment Principal",
                "ifc_filename": "batiment.ifc",
                "sensors": [
                    {
                        "sensor_type": "ble_node",
                        "unicast": "0x00A1",
                        "device_name": "Capteur Bureau 201",
                        "network_id": 2,
                        "sensor_types": ["Température", "Humidité"],
                    }
                ],
            }
        }
    }


# ──────────────────────────────────────────────
# Mapping salle (entrée — mise à jour)
# ──────────────────────────────────────────────

class MappingUpdate(BaseModel):
    space_name: Optional[str] = None
    space_long_name: Optional[str] = None
    storey_name: Optional[str] = None
    area_m2: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


# ──────────────────────────────────────────────
# Mapping salle (sortie)
# ──────────────────────────────────────────────

class MappingOut(BaseModel):
    id: int
    space_global_id: str
    space_name: str
    space_long_name: Optional[str] = None
    storey_name: Optional[str] = None
    area_m2: Optional[float] = None
    project_name: Optional[str] = None
    ifc_filename: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    sensors: List[SensorOut] = []

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Ajout / suppression de capteurs sur un mapping existant
# ──────────────────────────────────────────────

class AddSensorsRequest(BaseModel):
    sensors: List[SensorIn]


class RemoveSensorRequest(BaseModel):
    sensor_id: int = Field(..., description="ID de l'assignation à supprimer")


# ──────────────────────────────────────────────
# Import en masse (depuis le notebook etape3)
# ──────────────────────────────────────────────

class BulkMappingItem(BaseModel):
    space_global_id: str
    space_name: str
    sensors: List[SensorIn] = []


class BulkImportRequest(BaseModel):
    project_name: Optional[str] = None
    ifc_filename: Optional[str] = None
    mappings: List[BulkMappingItem]


class BulkImportResult(BaseModel):
    created: int
    updated: int
    errors: List[str] = []
