"""
Routes FastAPI — Mapping Service
CRUD complet + import en masse + export
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import crud
from app.models.schemas import (
    MappingCreate,
    MappingOut,
    MappingUpdate,
    AddSensorsRequest,
    BulkImportRequest,
    BulkImportResult,
)

router = APIRouter()


# ──────────────────────────────────────────────
# Lecture
# ──────────────────────────────────────────────

@router.get("/", response_model=List[MappingOut], summary="Tous les mappings")
def list_mappings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retourne la liste paginée de tous les mappings salle ↔ capteurs."""
    return crud.get_all_mappings(db, skip=skip, limit=limit)


@router.get("/{mapping_id}", response_model=MappingOut, summary="Détail d'un mapping par ID")
def get_mapping(mapping_id: int, db: Session = Depends(get_db)):
    mapping = crud.get_mapping_by_id(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping id={mapping_id} introuvable.")
    return mapping


@router.get(
    "/space/{space_global_id}",
    response_model=MappingOut,
    summary="Mapping par GlobalId IFC",
)
def get_mapping_by_space(space_global_id: str, db: Session = Depends(get_db)):
    """Cherche le mapping d'une salle par son GlobalId IFC."""
    mapping = crud.get_mapping_by_global_id(db, space_global_id)
    if not mapping:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun mapping pour la salle '{space_global_id}'.",
        )
    return mapping


# ──────────────────────────────────────────────
# Création
# ──────────────────────────────────────────────

@router.post("/", response_model=MappingOut, status_code=status.HTTP_201_CREATED,
             summary="Créer un mapping salle ↔ capteurs")
def create_mapping(data: MappingCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau mapping.  
    Si la salle est déjà mappée (même space_global_id), retourne 409.
    """
    existing = crud.get_mapping_by_global_id(db, data.space_global_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un mapping existe déjà pour la salle '{data.space_global_id}'. "
                   f"Utilisez PUT pour le modifier.",
        )
    return crud.create_mapping(db, data)


# ──────────────────────────────────────────────
# Mise à jour
# ──────────────────────────────────────────────

@router.put("/{mapping_id}", response_model=MappingOut, summary="Mettre à jour un mapping")
def update_mapping(mapping_id: int, data: MappingUpdate, db: Session = Depends(get_db)):
    """Met à jour les métadonnées d'un mapping (pas les capteurs)."""
    mapping = crud.get_mapping_by_id(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping introuvable.")
    return crud.update_mapping(db, mapping, data)


@router.post("/{mapping_id}/sensors", response_model=MappingOut,
             summary="Ajouter des capteurs à un mapping")
def add_sensors(mapping_id: int, body: AddSensorsRequest, db: Session = Depends(get_db)):
    """Ajoute un ou plusieurs capteurs à un mapping existant."""
    mapping = crud.get_mapping_by_id(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping introuvable.")
    crud.add_sensors(db, mapping_id, body.sensors)
    db.refresh(mapping)
    return mapping


@router.put("/{mapping_id}/sensors", response_model=MappingOut,
            summary="Remplacer tous les capteurs d'un mapping")
def replace_sensors(mapping_id: int, body: AddSensorsRequest, db: Session = Depends(get_db)):
    """Remplace entièrement la liste des capteurs d'un mapping."""
    mapping = crud.get_mapping_by_id(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping introuvable.")
    return crud.replace_sensors(db, mapping, body.sensors)


@router.delete("/{mapping_id}/sensors/{sensor_id}", summary="Supprimer un capteur d'un mapping")
def remove_sensor(mapping_id: int, sensor_id: int, db: Session = Depends(get_db)):
    """Supprime une assignation capteur spécifique."""
    mapping = crud.get_mapping_by_id(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping introuvable.")
    deleted = crud.remove_sensor(db, sensor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Capteur id={sensor_id} introuvable.")
    return {"message": f"Capteur {sensor_id} supprimé du mapping {mapping_id}."}


# ──────────────────────────────────────────────
# Suppression
# ──────────────────────────────────────────────

@router.delete("/{mapping_id}", summary="Supprimer un mapping")
def delete_mapping(mapping_id: int, db: Session = Depends(get_db)):
    """Supprime un mapping et tous ses capteurs associés."""
    mapping = crud.get_mapping_by_id(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping introuvable.")
    crud.delete_mapping(db, mapping)
    return {"message": f"Mapping id={mapping_id} supprimé."}


# ──────────────────────────────────────────────
# Import en masse (remplace etape3.ipynb MANUAL_MAPPING)
# ──────────────────────────────────────────────

@router.post("/bulk-import", response_model=BulkImportResult,
             summary="Import en masse de mappings")
def bulk_import(body: BulkImportRequest, db: Session = Depends(get_db)):
    """
    Importe une liste complète de mappings en une seule requête.  
    - Crée les mappings inexistants.  
    - Met à jour et remplace les capteurs des mappings déjà existants.  
    
    Idéal pour migrer le `MANUAL_MAPPING` de l'ancien notebook etape3.
    """
    result = crud.bulk_import(
        db,
        items=body.mappings,
        project_name=body.project_name or "",
        ifc_filename=body.ifc_filename or "",
    )
    return result


# ──────────────────────────────────────────────
# Export complet
# ──────────────────────────────────────────────

@router.get("/export/json", summary="Exporter tous les mappings en JSON")
def export_mappings(db: Session = Depends(get_db)):
    """
    Exporte l'intégralité du mapping en JSON téléchargeable.
    Format compatible avec le jumeau numérique.
    """
    mappings = crud.get_all_mappings(db, skip=0, limit=10000)

    export_data = {
        "total": len(mappings),
        "mappings": [
            {
                "space_global_id": m.space_global_id,
                "space_name": m.space_name,
                "storey_name": m.storey_name,
                "area_m2": m.area_m2,
                "sensors": [
                    {
                        "sensor_type": s.sensor_type,
                        "unicast": s.unicast,
                        "device_name": s.device_name,
                        "network_id": s.network_id,
                        "sensor_types": s.sensor_types_str.split(",") if s.sensor_types_str else [],
                    }
                    for s in m.sensors
                ],
            }
            for m in mappings
        ],
    }

    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": "attachment; filename=mapping_export.json"
        },
    )


@router.get("/stats/summary", summary="Statistiques du mapping")
def get_stats(db: Session = Depends(get_db)):
    """Retourne des statistiques globales sur les mappings."""
    mappings = crud.get_all_mappings(db, skip=0, limit=10000)
    total_sensors = sum(len(m.sensors) for m in mappings)
    mapped_spaces = [m for m in mappings if m.sensors]
    unmapped_spaces = [m for m in mappings if not m.sensors]

    return {
        "total_spaces": len(mappings),
        "spaces_with_sensors": len(mapped_spaces),
        "spaces_without_sensors": len(unmapped_spaces),
        "total_sensor_assignments": total_sensors,
        "active_mappings": sum(1 for m in mappings if m.is_active),
    }
