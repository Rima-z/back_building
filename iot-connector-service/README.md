# IoT Connector Service — Microservice 2

Microservice FastAPI pour la connexion à la plateforme **WaveOn IoT**.  
Gère l'authentification, la récupération des réseaux, SmartControllers et capteurs BLE Mesh.

---

## Prérequis

- Python 3.11.5
- Windows 11
- Compte WaveOn actif

---

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration

Copier `.env.example` en `.env` et renseigner les variables :

```bash
copy .env.example .env
```

---

## Lancement

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

API disponible sur : http://localhost:8002  
Documentation Swagger : http://localhost:8002/docs

---

## Flux d'utilisation

```
1. POST /api/iot/connect          → Authentification → retourne session_id
2. GET  /api/iot/networks/{sid}   → Liste des réseaux
3. GET  /api/iot/sensors/{sid}    → Capteurs BLE Mesh
4. GET  /api/iot/controllers/{sid}→ SmartControllers (compteurs)
5. GET  /api/iot/devices/{sid}    → Tout consolidé en un seul appel
```

---

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/iot/connect` | Authentification WaveOn |
| `GET` | `/api/iot/networks/{session_id}` | Liste des réseaux |
| `GET` | `/api/iot/sensors/{session_id}` | Capteurs BLE Mesh |
| `GET` | `/api/iot/controllers/{session_id}` | SmartControllers |
| `GET` | `/api/iot/devices/{session_id}` | Tous les équipements consolidés |
| `GET` | `/api/iot/sessions` | Sessions actives |
| `DELETE` | `/api/iot/sessions/{session_id}` | Déconnexion |

---

## Exemple d'utilisation

```bash
# 1. Connexion
curl -X POST http://localhost:8002/api/iot/connect \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"motdepasse"}'

# Réponse : { "session_id": "abc123...", "id_client": 5 }

# 2. Récupérer tous les équipements
curl http://localhost:8002/api/iot/devices/abc123...
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Docker

```bash
docker build -t iot-connector-service .
docker run -p 8002:8002 iot-connector-service
```
