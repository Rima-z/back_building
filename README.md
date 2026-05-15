# Jumeau Numérique — Backend Microservices

Architecture microservices Python/FastAPI pour le jumeau numérique BIM/IoT.

---

## Architecture

```
digital-twin/
├── ifc-parser-service/       Port 8001 — Parsing fichiers IFC
├── iot-connector-service/    Port 8002 — Connexion WaveOn IoT
├── mapping-service/          Port 8003 — Mapping Salle ↔ Capteurs (PostgreSQL)
└── docker-compose.yml        Orchestration complète
```

### Flux de données

```
Fichier IFC  ──►  ifc-parser-service  ──►  liste des salles (GlobalId, nom, étage)
                                                    │
WaveOn API   ──►  iot-connector-service ──►  liste des capteurs (unicast, type)
                                                    │
                                          mapping-service  ──►  PostgreSQL
                                          (Salle ↔ Capteur)
```

---

## Démarrage rapide (sans Docker)

### Prérequis

- Python 3.11.5
- PostgreSQL 18
- Windows 11

### 1. IFC Parser Service

```bash
cd ifc-parser-service    
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
→ http://localhost:8001/docs

### 2. IoT Connector Service

```bash
cd iot-connector-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```
→ http://localhost:8002/docs

### 3. Mapping Service

```bash
cd mapping-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env         # Configurer DATABASE_URL
python init_db.py              # Créer les tables PostgreSQL
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```
→ http://localhost:8003/docs

---

## Démarrage avec Docker

```bash
docker-compose up --build
```

Services disponibles :
- IFC Parser  → http://localhost:8001/docs
- IoT WaveOn  → http://localhost:8002/docs
- Mapping     → http://localhost:8003/docs

---

## Workflow typique

### Étape 1 — Parser le fichier IFC

```bash
curl -X POST http://localhost:8001/api/ifc/upload \
  -F "file=@MonBatiment.ifc"
# → { "session_id": "abc...", "hierarchy": { "levels": [...] } }
```

### Étape 2 — Récupérer les capteurs WaveOn

```bash
curl -X POST http://localhost:8002/api/iot/connect \
  -H "Content-Type: application/json" \
  -d '{"email":"user@waveon.tn","password":"pass"}'
# → { "session_id": "xyz..." }

curl http://localhost:8002/api/iot/devices/xyz...
# → { "sensors": [...], "smart_controllers": [...] }
```

### Étape 3 — Créer le mapping

```bash
curl -X POST http://localhost:8003/api/mapping/ \
  -H "Content-Type: application/json" \
  -d '{
    "space_global_id": "2BuScNrX9BOfc20VVyh05w",
    "space_name": "Bureau 201",
    "storey_name": "Niveau 2",
    "sensors": [{
      "sensor_type": "ble_node",
      "unicast": "0x00A1",
      "device_name": "Capteur Bureau 201",
      "network_id": 2,
      "sensor_types": ["Température", "Humidité"]
    }]
  }'
```

### Étape 4 — Exporter le mapping

```bash
curl http://localhost:8003/api/mapping/export/json > mapping_export.json
```

---

## Tests

```bash
# Chaque service a ses propres tests
cd ifc-parser-service && pytest tests/ -v
cd iot-connector-service && pytest tests/ -v
cd mapping-service && pytest tests/ -v   # Utilise SQLite en mémoire
```

---

## Ports utilisés

| Service | Port | Documentation |
|---------|------|---------------|
| IFC Parser | 8001 | http://localhost:8001/docs |
| IoT Connector | 8002 | http://localhost:8002/docs |
| Mapping | 8003 | http://localhost:8003/docs |
| PostgreSQL | 5433 | — |
