"""
Couche CRUD — toutes les opérations sur la base de données
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.orm_models import SpaceMapping, SensorAssignment
from app.models.schemas import MappingCreate, MappingUpdate, SensorIn
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# SpaceMapping CRUD
# ──────────────────────────────────────────────

def get_all_mappings(db: Session, skip: int = 0, limit: int = 100) -> List[SpaceMapping]:
    return db.query(SpaceMapping).offset(skip).limit(limit).all()


def get_mapping_by_id(db: Session, mapping_id: int) -> Optional[SpaceMapping]:
    return db.query(SpaceMapping).filter(SpaceMapping.id == mapping_id).first()


def get_mapping_by_global_id(db: Session, space_global_id: str) -> Optional[SpaceMapping]:
    return db.query(SpaceMapping).filter(
        SpaceMapping.space_global_id == space_global_id
    ).first()


def create_mapping(db: Session, data: MappingCreate) -> SpaceMapping:
    """Crée un nouveau mapping salle + ses capteurs en une transaction."""
    mapping = SpaceMapping(
        space_global_id=data.space_global_id,
        space_name=data.space_name,
        space_long_name=data.space_long_name,
        storey_name=data.storey_name,
        area_m2=data.area_m2,
        project_name=data.project_name,
        ifc_filename=data.ifc_filename,
        notes=data.notes,
    )
    db.add(mapping)
    db.flush()  # Obtenir l'id avant commit

    for sensor_in in data.sensors:
        _add_sensor_to_mapping(db, mapping.id, sensor_in)

    db.commit()
    db.refresh(mapping)
    logger.info(f"Mapping créé : {mapping.space_name} ({mapping.space_global_id})")
    return mapping


def update_mapping(db: Session, mapping: SpaceMapping, data: MappingUpdate) -> SpaceMapping:
    """Met à jour les champs d'un mapping existant (sans toucher aux capteurs)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)
    db.commit()
    db.refresh(mapping)
    return mapping


def delete_mapping(db: Session, mapping: SpaceMapping) -> None:
    """Supprime un mapping et tous ses capteurs (cascade)."""
    db.delete(mapping)
    db.commit()
    logger.info(f"Mapping supprimé : {mapping.space_global_id}")


# ──────────────────────────────────────────────
# SensorAssignment CRUD
# ──────────────────────────────────────────────

def add_sensors(db: Session, mapping_id: int, sensors: List[SensorIn]) -> List[SensorAssignment]:
    """Ajoute une liste de capteurs à un mapping existant."""
    created = []
    for sensor_in in sensors:
        assignment = _add_sensor_to_mapping(db, mapping_id, sensor_in)
        created.append(assignment)
    db.commit()
    for a in created:
        db.refresh(a)
    return created


def remove_sensor(db: Session, sensor_id: int) -> bool:
    """Supprime une assignation capteur par son id."""
    assignment = db.query(SensorAssignment).filter(SensorAssignment.id == sensor_id).first()
    if not assignment:
        return False
    db.delete(assignment)
    db.commit()
    return True


def replace_sensors(db: Session, mapping: SpaceMapping, sensors: List[SensorIn]) -> SpaceMapping:
    """Remplace tous les capteurs d'un mapping par la nouvelle liste."""
    for existing in mapping.sensors:
        db.delete(existing)
    db.flush()

    for sensor_in in sensors:
        _add_sensor_to_mapping(db, mapping.id, sensor_in)

    db.commit()
    db.refresh(mapping)
    return mapping


# ──────────────────────────────────────────────
# Import en masse
# ──────────────────────────────────────────────

def bulk_import(db: Session, items: list, project_name: str, ifc_filename: str) -> dict:
    """
    Importe une liste de mappings.
    - Crée si le space_global_id n'existe pas encore.
    - Met à jour et remplace les capteurs si déjà existant.
    """
    created = 0
    updated = 0
    errors = []

    for item in items:
        try:
            existing = get_mapping_by_global_id(db, item.space_global_id)
            if existing:
                replace_sensors(db, existing, item.sensors)
                updated += 1
            else:
                create_mapping(
                    db,
                    MappingCreate(
                        space_global_id=item.space_global_id,
                        space_name=item.space_name,
                        project_name=project_name,
                        ifc_filename=ifc_filename,
                        sensors=item.sensors,
                    ),
                )
                created += 1
        except Exception as e:
            logger.error(f"Erreur bulk import {item.space_global_id}: {e}")
            errors.append(f"{item.space_global_id}: {str(e)}")
            db.rollback()

    return {"created": created, "updated": updated, "errors": errors}


# ──────────────────────────────────────────────
# Helper interne
# ──────────────────────────────────────────────

def _add_sensor_to_mapping(db: Session, mapping_id: int, sensor_in: SensorIn) -> SensorAssignment:
    sensor_types_str = ",".join(sensor_in.sensor_types) if sensor_in.sensor_types else ""
    assignment = SensorAssignment(
        space_mapping_id=mapping_id,
        sensor_type=sensor_in.sensor_type,
        device_id=sensor_in.device_id,
        unicast=sensor_in.unicast,
        device_name=sensor_in.device_name,
        network_id=sensor_in.network_id,
        pid_label=sensor_in.pid_label,
        sensor_types_str=sensor_types_str,
        notes=sensor_in.notes,
    )
    db.add(assignment)
    db.flush()
    return assignment
