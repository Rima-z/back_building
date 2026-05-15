"""
Client WaveOn IoT — adapté depuis etape2.ipynb
Gère l'authentification et la récupération des capteurs
"""

import json
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://iot.waveon.tn/WS_WAVEON"
REF_DATE = "2019-10-01 01:01:01"

# ──────────────────────────────────────────────
# Dictionnaires de types
# ──────────────────────────────────────────────

MODEL_TYPES = {
    "1002": "Contrôle générique",
    "590011": "Humidité",
    "590012": "Température",
    "590013": "Présence/Occupation",
    "590014": "Luminosité",
    "590015": "Compteur",
    "590016": "Volets roulants",
    "590018": "Comptage énergie/eau",
    "00590011": "Humidité",
    "00590012": "Température",
    "00590013": "Présence/Occupation",
    "00590014": "Luminosité",
    "00590015": "Compteur",
    "00590016": "Volets roulants",
    "00590018": "Comptage énergie/eau",
}

PID_TYPES = {
    "0000": "Équipement générique",
    "0001": "Télécommande",
    "0002": "Interrupteur/Capteur/Dimmer",
    "0003": "Volet roulant",
    "0004": "Booster signal",
    "0005": "Double lampe",
    "0007": "Climatiseur",
    "0008": "Actionneur de porte",
    "0009": "Capteur de porte",
}

PRODUCT_NAMES = {
    12: "SmartMeter (électricité)",
    13: "Débitmètre (eau)",
}


# ──────────────────────────────────────────────
# Authentification
# ──────────────────────────────────────────────

def authenticate(email: str, password: str, device_name: str = "digital-twin-service") -> dict:
    """
    Authentification à l'API WaveOn.
    Retourne idclient, iduser, token.
    """
    logger.info(f"Authentification WaveOn pour: {email}")

    resp = requests.post(
        f"{BASE_URL}/LoginClientService/",
        json={
            "email": email,
            "password": password,
            "devicename": device_name,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        raise Exception(f"Authentification échouée [{resp.status_code}]: {resp.text}")

    auth = resp.json()
    logger.info(f"Connecté — idclient={auth.get('idclient')}, iduser={auth.get('iduser')}")

    return {
        "id_client": auth["idclient"],
        "id_user": auth["iduser"],
        "token": auth["token"],
        "database_ip": auth.get("databaseIP"),
        "database_port": auth.get("databasePORT"),
    }


# ──────────────────────────────────────────────
# Réseaux
# ──────────────────────────────────────────────

def get_networks(id_client: int, id_user: int, token: str, id_network: int = 2) -> list:
    """Récupère tous les réseaux WaveOn disponibles."""
    resp = requests.post(
        f"{BASE_URL}/getNetworksInfoService/",
        json={
            "idclient": id_client,
            "iduser": id_user,
            "token": token,
            "idNetwork": id_network,
            "lastupdate": REF_DATE,
            "commandLastId": 0,
            "permissionsLastUpdate": REF_DATE,
            "roomsLastUpdate": REF_DATE,
            "automationLastUpdate": REF_DATE,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        raise Exception(f"Erreur récupération réseaux [{resp.status_code}]: {resp.text}")

    networks_raw = resp.json()
    return [
        {
            "id_network": net["idNetwork"],
            "name": net.get("name", f"Réseau {net['idNetwork']}"),
            "last_update": net.get("lastUpdate"),
        }
        for net in networks_raw
    ]


# ──────────────────────────────────────────────
# SmartControllers (compteurs)
# ──────────────────────────────────────────────

def get_smart_controllers(id_client: int, id_user: int, token: str, networks: list) -> list:
    """Récupère tous les SmartControllers (compteurs énergie/eau) pour tous les réseaux."""
    all_controllers = []

    for net in networks:
        id_network = net["id_network"]
        logger.info(f"Récupération SmartControllers du réseau [{id_network}]")

        resp = requests.post(
            f"{BASE_URL}/ClientGetAllSmartControllerService/",
            json={
                "idclient": id_client,
                "iduser": id_user,
                "idNetwork": id_network,
                "token": token,
                "lastUpdate": REF_DATE,
                "commandLastId": 0,
                "permissionsLastUpdate": REF_DATE,
                "roomsLastUpdate": REF_DATE,
                "automationLastUpdate": REF_DATE,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            logger.warning(f"Erreur réseau [{id_network}]: {resp.status_code}")
            continue

        ctrl_data = resp.json()
        controllers = ctrl_data.get("controllers", [])

        for ctrl in controllers:
            product_label = PRODUCT_NAMES.get(
                ctrl.get("productId"), ctrl.get("productName", "Inconnu")
            )
            meter_config = {}
            if ctrl.get("meterConfig"):
                try:
                    meter_config = json.loads(ctrl["meterConfig"])
                except (json.JSONDecodeError, TypeError):
                    pass

            variables = meter_config.get("var", [])

            all_controllers.append(
                {
                    "id_network": id_network,
                    "id_smart_controller": ctrl.get("idSmartController"),
                    "unicast": ctrl.get("unicast"),
                    "name": ctrl.get("name", "Inconnu"),
                    "product_id": ctrl.get("productId"),
                    "product_name": product_label,
                    "sn": ctrl.get("sn"),
                    "enabled": bool(ctrl.get("enabled", False)),
                    "variables": variables,
                    "meter_config": meter_config,
                }
            )

    logger.info(f"Total SmartControllers: {len(all_controllers)}")
    return all_controllers


# ──────────────────────────────────────────────
# Capteurs BLE Mesh
# ──────────────────────────────────────────────

def _parse_sensor_types(node: dict) -> list:
    """Décode les types de capteurs depuis modelID et éléments."""
    sensor_types = set()

    # Depuis elements (liste de sous-capteurs)
    for elem in node.get("elements", []):
        for model in elem.get("models", []):
            mid = str(model.get("modelId", "")).strip().upper()
            
            # Essayer plusieurs formats possibles
            candidates = [
                mid,                          # tel quel ex: "1002"
                mid.lower(),                  # lowercase ex: "1002"
                mid.lstrip("0").lower(),      # sans zéros ex: "590011"
                mid.zfill(8).lower(),         # 8 chars ex: "00001002"
            ]
            
            for candidate in candidates:
                if candidate in MODEL_TYPES:
                    sensor_types.add(MODEL_TYPES[candidate])
                    break

    return list(sensor_types)

def get_ble_nodes(id_client: int, id_user: int, token: str, networks: list) -> list:
    """Récupère tous les noeuds BLE Mesh via downloadMultiNetworkFile."""
    all_nodes = []

    for net in networks:
        id_network = net["id_network"]
        logger.info(f"Récupération capteurs BLE du réseau [{id_network}]")

        resp = requests.post(
            f"{BASE_URL}/downloadMultiNetworkFile/",  # ✅ le bon endpoint
            json={
                "idclient": id_client,
                "iduser": id_user,
                "token": token,
                "lastupdate": REF_DATE,
                "idNetwork": id_network,
                "permissionsLastUpdate": REF_DATE,
                "roomsLastUpdate": REF_DATE,
                "automationLastUpdate": REF_DATE,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            logger.warning(f"Erreur BLE réseau [{id_network}]: {resp.status_code}")
            continue

        mesh_data = resp.json()
        nodes = mesh_data.get("nodes", [])

        for node in nodes:
            unicast_hex = node.get("unicastAddress") or node.get("unicast")
            unicast_dec = None
            if unicast_hex:
                try:
                    unicast_dec = int(str(unicast_hex), 16)
                except (ValueError, TypeError):
                    unicast_dec = None

            pid = str(node.get("pid", "")).zfill(4)
            pid_label = PID_TYPES.get(pid, f"Type inconnu ({pid})")
            sensor_types = _parse_sensor_types(node)

            all_nodes.append({
                "id_network": id_network,
                "id_ble_node": node.get("id"),
                "unicast_hex": str(unicast_hex) if unicast_hex else None,
                "unicast_dec": unicast_dec,
                "name": node.get("name", f"Nœud {unicast_hex}"),
                "pid": pid,
                "pid_label": pid_label,
                "sensor_types": sensor_types,
                "enabled": bool(node.get("enabled", True)),
            })

    logger.info(f"Total capteurs BLE: {len(all_nodes)}")
    return all_nodes
