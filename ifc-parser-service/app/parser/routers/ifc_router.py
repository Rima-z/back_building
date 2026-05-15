"""
Routes FastAPI pour le IFC Parser Service
"""

import os
import uuid
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from app.parser.ifc_reader import parse_ifc_file
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Stockage temporaire en mémoire des résultats parsés (clé = session_id)
_parsed_cache: dict = {}

ALLOWED_EXTENSIONS = {".ifc"}
MAX_FILE_SIZE_MB = 500


@router.post("/upload", summary="Upload et parse un fichier IFC")
async def upload_ifc(file: UploadFile = File(...)):
    """
    Upload un fichier IFC et retourne la hiérarchie complète du bâtiment.

    - **file**: Fichier .ifc à analyser
    
    Retourne la structure Project > Site > Building > Storey > Space
    ainsi que la liste des équipements techniques détectés.
    """
    # Validation extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension non supportée '{ext}'. Seuls les fichiers .ifc sont acceptés.",
        )

    # Sauvegarde temporaire
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}{ext}")

    try:
        with open(tmp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Vérification taille
        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        logger.info(f"Fichier reçu: {file.filename} ({size_mb:.2f} MB)")

        # Parsing
        result = parse_ifc_file(tmp_path)

        # Mise en cache avec session_id
        session_id = uuid.uuid4().hex
        _parsed_cache[session_id] = result
        result["session_id"] = session_id
        result["original_filename"] = file.filename

        return JSONResponse(content=result, status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erreur parsing IFC: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du parsing IFC: {str(e)}",
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/spaces/{session_id}", summary="Liste des espaces d'une session parsée")
def get_spaces(session_id: str):
    """
    Retourne la liste de tous les espaces/pièces extraits d'une session IFC.
    Utilisez le session_id retourné par /upload.
    """
    data = _parsed_cache.get(session_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' introuvable. Veuillez re-uploader le fichier IFC.",
        )

    spaces = []
    for level in data["hierarchy"]["levels"]:
        for sp in level.get("spaces", []):
            spaces.append({**sp, "storey_name": level["name"]})
    for sp in data["hierarchy"].get("unassigned_spaces", []):
        spaces.append({**sp, "storey_name": "Non assigné"})

    return {
        "session_id": session_id,
        "total": len(spaces),
        "spaces": spaces,
    }


@router.get("/spaces/{session_id}/{space_global_id}", summary="Détail d'un espace")
def get_space_detail(session_id: str, space_global_id: str):
    """Retourne le détail d'un espace spécifique par son GlobalId IFC."""
    data = _parsed_cache.get(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    all_spaces = []
    for level in data["hierarchy"]["levels"]:
        all_spaces.extend(level.get("spaces", []))
    all_spaces.extend(data["hierarchy"].get("unassigned_spaces", []))

    space = next((s for s in all_spaces if s["global_id"] == space_global_id), None)
    if not space:
        raise HTTPException(
            status_code=404,
            detail=f"Espace '{space_global_id}' introuvable dans la session.",
        )
    return space


@router.get("/equipment/{session_id}", summary="Liste des équipements techniques")
def get_equipment(session_id: str):
    """Retourne tous les équipements techniques extraits du fichier IFC."""
    data = _parsed_cache.get(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    return {
        "session_id": session_id,
        "total": len(data["equipment"]),
        "equipment": data["equipment"],
    }


@router.get("/hierarchy/{session_id}", summary="Hiérarchie complète du bâtiment")
def get_hierarchy(session_id: str):
    """Retourne la hiérarchie complète Project > Storey > Space."""
    data = _parsed_cache.get(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    return {
        "session_id": session_id,
        "schema": data["schema"],
        "summary": data["summary"],
        "hierarchy": data["hierarchy"],
    }


@router.get("/sessions", summary="Liste des sessions actives en mémoire")
def list_sessions():
    """Liste les sessions IFC parsées et disponibles en cache."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "filename": d.get("original_filename", "?"),
                "storeys": d["summary"]["storeys"],
                "spaces": d["summary"]["spaces"],
            }
            for sid, d in _parsed_cache.items()
        ]
    }