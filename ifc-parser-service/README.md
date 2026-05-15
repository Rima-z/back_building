# IFC Parser Service — Microservice 1

Microservice FastAPI pour le parsing de fichiers IFC (BIM).  
Extrait la hiérarchie spatiale : **Project → Site → Building → Storey → Space** + équipements techniques.

---

## Prérequis

- Python 3.11.5
- Windows 11

---

## Installation

```bash
# Créer et activer l'environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## Lancement

```bash
# Depuis le dossier ifc-parser-service/
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

L'API sera disponible sur : http://localhost:8001  
Documentation Swagger : http://localhost:8001/docs

---

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/api/ifc/upload` | Upload + parse un fichier .ifc |
| `GET` | `/api/ifc/spaces/{session_id}` | Liste des espaces |
| `GET` | `/api/ifc/spaces/{session_id}/{global_id}` | Détail d'un espace |
| `GET` | `/api/ifc/equipment/{session_id}` | Équipements techniques |
| `GET` | `/api/ifc/hierarchy/{session_id}` | Hiérarchie complète |
| `GET` | `/api/ifc/sessions` | Sessions actives en cache |

---

## Exemple d'utilisation

```bash
# Upload d'un fichier IFC
curl -X POST http://localhost:8001/api/ifc/upload \
  -F "file=@MonBatiment.ifc"

# Réponse : { "session_id": "abc123...", "summary": {...}, "hierarchy": {...} }

# Récupérer les espaces
curl http://localhost:8001/api/ifc/spaces/abc123...
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Docker

```bash
docker build -t ifc-parser-service .
docker run -p 8001:8001 ifc-parser-service
```