"""
Modèles Pydantic pour le IoT Connector Service
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ──────────────────────────────────────────────
# Authentification
# ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str
    device_name: str = "digital-twin-service"

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "motdepasse",
                "device_name": "digital-twin-service",
            }
        }
    }


class LoginResponse(BaseModel):
    id_client: int
    id_user: int
    token: str
    database_ip: Optional[str] = None
    database_port: Optional[int] = None


class SessionCredentials(BaseModel):
    """Credentials réutilisés dans les requêtes suivantes."""
    id_client: int
    id_user: int
    token: str


# ──────────────────────────────────────────────
# Réseaux
# ──────────────────────────────────────────────

class NetworkInfo(BaseModel):
    id_network: int
    name: str
    last_update: Optional[str] = None


# ──────────────────────────────────────────────
# SmartControllers (compteurs énergie/eau)
# ──────────────────────────────────────────────

class SmartControllerInfo(BaseModel):
    id_network: int
    id_smart_controller: int
    unicast: int
    name: str
    product_id: int
    product_name: str
    sn: Optional[str] = None
    enabled: bool
    variables: List[str] = []
    meter_config: Optional[Dict[str, Any]] = {}


# ──────────────────────────────────────────────
# Capteurs BLE Mesh
# ──────────────────────────────────────────────

class BLENodeInfo(BaseModel):
    id_network: int
    id_ble_node: Optional[int] = None
    unicast_hex: Optional[str] = None
    unicast_dec: Optional[int] = None
    name: str
    model_id: Optional[str] = None
    pid: Optional[str] = None
    pid_label: Optional[str] = None
    sensor_types: List[str] = []
    enabled: bool = True
    raw: Optional[Dict[str, Any]] = {}


# ──────────────────────────────────────────────
# Réponses consolidées
# ──────────────────────────────────────────────

class AllDevicesResponse(BaseModel):
    session_id: str
    networks: List[NetworkInfo] = []
    smart_controllers: List[SmartControllerInfo] = []
    ble_nodes: List[BLENodeInfo] = []
    summary: Dict[str, int] = {}
