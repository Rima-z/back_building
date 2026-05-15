# Mapping Service — Microservice 3

Microservice FastAPI avec persistance **PostgreSQL** pour le mapping **Salle IFC ↔ Capteurs WaveOn**.  
Remplace le `MANUAL_MAPPING` codé en dur dans l'ancien notebook `etape3.ipynb`.

---

## Prérequis

- Python 3.11.5
- PostgreSQL 18 (installé et en cours d'exécution)
- Windows 11

---

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration PostgreSQL

### 1. Créer la base de données

Ouvrir pgAdmin ou psql et exécuter :

```sql
CREATE DATABASE digital_twin_mapping;
```

### 2. Configurer le .env

```bash
copy .env.example .env
```

Éditer `.env` et renseigner :

```
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/digital_twin_mapping
```

### 3. Initialiser les tables

```bash
python init_db.py
```

---

## Lancement

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

API disponible sur : http://localhost:8003  
Documentation Swagger : http://localhost:8003/docs

---

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/mapping/` | Tous les mappings |
| `GET` | `/api/mapping/{id}` | Mapping par ID |
| `GET` | `/api/mapping/space/{global_id}` | Mapping par GlobalId IFC |
| `POST` | `/api/mapping/` | Créer un mapping |
| `PUT` | `/api/mapping/{id}` | Modifier un mapping |
| `DELETE` | `/api/mapping/{id}` | Supprimer un mapping |
| `POST` | `/api/mapping/{id}/sensors` | Ajouter des capteurs |
| `PUT` | `/api/mapping/{id}/sensors` | Remplacer les capteurs |
| `DELETE` | `/api/mapping/{id}/sensors/{sid}` | Supprimer un capteur |
| `POST` | `/api/mapping/bulk-import` | Import en masse |
| `GET` | `/api/mapping/export/json` | Export JSON complet |
| `GET` | `/api/mapping/stats/summary` | Statistiques |

---

## Structure de la base de données

```
space_mappings
├── id (PK)
├── space_global_id (unique — GlobalId IFC)
├── space_name
├── storey_name
├── area_m2
├── project_name
├── ifc_filename
├── is_active
├── notes
├── created_at
└── updated_at

sensor_assignments
├── id (PK)
├── space_mapping_id (FK → space_mappings)
├── sensor_type (ble_node | smart_controller)
├── unicast
├── device_name
├── network_id
├── sensor_types_str
├── pid_label
└── assigned_at
```

---

## Exemple d'utilisation

```bash
# Créer un mapping
curl -X POST http://localhost:8003/api/mapping/ \
  -H "Content-Type: application/json" \
  -d '{
    "space_global_id": "2BuScNrX9BOfc20VVyh05w",
    "space_name": "Bureau 201",
    "storey_name": "Niveau 2",
    "area_m2": 32.5,
    "sensors": [{
      "sensor_type": "ble_node",
      "unicast": "0x00A1",
      "device_name": "Capteur Bureau 201",
      "network_id": 2,
      "sensor_types": ["Température", "Humidité"]
    }]
  }'

# Exporter tout le mapping
curl http://localhost:8003/api/mapping/export/json
```

---

## Migrer depuis etape3.ipynb

Utilisez l'endpoint `/api/mapping/bulk-import` avec votre ancien `MANUAL_MAPPING` converti en JSON :

```bash
curl -X POST http://localhost:8003/api/mapping/bulk-import \
  -H "Content-Type: application/json" \
  -d @mon_mapping_migre.json
```

---

## Tests

```bash
# Les tests utilisent SQLite en mémoire (pas besoin de PostgreSQL)
pytest tests/ -v
```

---

## Docker

```bash
docker build -t mapping-service .
docker run -p 8003:8003 \
  -e DATABASE_URL=postgresql://postgres:pass@host.docker.internal:5432/digital_twin_mapping \
  mapping-service
```
