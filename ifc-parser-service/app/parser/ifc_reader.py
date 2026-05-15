"""
Logique de parsing IFC — adaptée depuis etape1.ipynb
Utilise ifcopenshell pour extraire la hiérarchie spatiale du bâtiment
"""

import ifcopenshell
import ifcopenshell.util.element
from typing import Optional
import logging

logger = logging.getLogger(__name__)

EQUIPMENT_TYPES = [
    "IfcFlowTerminal",
    "IfcEnergyConversionDevice",
    "IfcFlowMovingDevice",
    "IfcSensor",
    "IfcActuator",
    "IfcController",
]


def safe_by_type(model, ifc_type: str) -> list:
    """Retourne les entites d'un type IFC, ou [] si le schema ne le supporte pas."""
    try:
        return model.by_type(ifc_type)
    except RuntimeError as exc:
        logger.warning(
            "Type IFC ignore car absent du schema %s: %s (%s)",
            model.schema,
            ifc_type,
            exc,
        )
        return []


def extract_project_info(model) -> dict:
    """Extrait les métadonnées du projet IFC."""
    project = model.by_type("IfcProject")[0]
    sites = model.by_type("IfcSite")
    buildings = model.by_type("IfcBuilding")

    return {
        "project_name": project.Name or "Sans nom",
        "global_id": project.GlobalId,
        "description": project.Description or "",
        "sites": [
            {
                "name": s.Name or "Site",
                "global_id": s.GlobalId,
                "description": s.Description or "",
            }
            for s in sites
        ],
        "buildings": [
            {
                "name": b.Name or "Bâtiment",
                "global_id": b.GlobalId,
                "description": b.Description or "",
            }
            for b in buildings
        ],
    }


def extract_storeys(model) -> list:
    """Extrait et trie les étages par élévation."""
    storeys = []
    for storey in model.by_type("IfcBuildingStorey"):
        elevation = float(storey.Elevation) if storey.Elevation is not None else None
        storeys.append(
            {
                "global_id": storey.GlobalId,
                "name": storey.Name or f"Étage {storey.id()}",
                "elevation_m": elevation,
                "description": storey.Description or "",
            }
        )
    storeys.sort(key=lambda x: x["elevation_m"] or 0)
    return storeys


def extract_spaces(model) -> list:
    """Extrait tous les espaces/pièces avec leurs propriétés."""
    spaces = []
    for space in model.by_type("IfcSpace"):
        # Trouver l'étage parent
        parent_storey = None
        for rel in model.by_type("IfcRelContainedInSpatialStructure"):
            if space in rel.RelatedElements:
                container = rel.RelatingStructure
                if container.is_a("IfcBuildingStorey"):
                    parent_storey = {
                        "name": container.Name,
                        "global_id": container.GlobalId,
                    }
                break

        # Propriétés (surface, volume)
        psets = ifcopenshell.util.element.get_psets(space)
        area = None
        volume = None
        for pset_name, props in psets.items():
            area = props.get("NetFloorArea") or props.get("Area") or area
            volume = props.get("Volume") or volume

        # Conversion sécurisée
        try:
            area = float(area) if area is not None else None
        except (TypeError, ValueError):
            area = None

        try:
            volume = float(volume) if volume is not None else None
        except (TypeError, ValueError):
            volume = None

        spaces.append(
            {
                "global_id": space.GlobalId,
                "name": space.Name or f"Espace {space.id()}",
                "long_name": space.LongName or "",
                "description": space.Description or "",
                "storey": parent_storey,
                "area_m2": area,
                "volume_m3": volume,
                "property_sets": {
                    k: {
                        pk: str(pv) if not isinstance(pv, (int, float, bool, str, type(None))) else pv
                        for pk, pv in v.items()
                    }
                    for k, v in psets.items()
                },
            }
        )
    return spaces


def extract_equipment(model) -> list:
    """Extrait tous les équipements techniques."""
    all_equipment = []
    for eq_type in EQUIPMENT_TYPES:
        for el in safe_by_type(model, eq_type):
            psets = ifcopenshell.util.element.get_psets(el)
            all_equipment.append(
                {
                    "ifc_type": eq_type,
                    "global_id": el.GlobalId,
                    "name": el.Name or f"{eq_type} {el.id()}",
                    "description": el.Description or "",
                    "property_sets": {
                        k: {
                            pk: str(pv) if not isinstance(pv, (int, float, bool, str, type(None))) else pv
                            for pk, pv in v.items()
                        }
                        for k, v in psets.items()
                    },
                }
            )
    return all_equipment


def build_hierarchy(project_info: dict, storeys: list, spaces: list) -> dict:
    """Construit la hiérarchie complète Project > Storey > Space."""
    hierarchy = {"project": project_info, "levels": [], "unassigned_spaces": []}

    for storey in storeys:
        level_spaces = [
            s
            for s in spaces
            if s["storey"] and s["storey"]["global_id"] == storey["global_id"]
        ]
        hierarchy["levels"].append({**storey, "spaces": level_spaces})

    hierarchy["unassigned_spaces"] = [s for s in spaces if not s["storey"]]
    return hierarchy


def parse_ifc_file(file_path: str) -> dict:
    """
    Fonction principale : parse un fichier IFC et retourne la structure complète.
    Adaptée depuis etape1.ipynb.
    """
    logger.info(f"Parsing IFC file: {file_path}")

    model = ifcopenshell.open(file_path)
    logger.info(f"Schema: {model.schema}")

    project_info = extract_project_info(model)
    storeys = extract_storeys(model)
    spaces = extract_spaces(model)
    equipment = extract_equipment(model)
    hierarchy = build_hierarchy(project_info, storeys, spaces)

    result = {
        "ifc_file": file_path,
        "schema": model.schema,
        "summary": {
            "storeys": len(storeys),
            "spaces": len(spaces),
            "equipment": len(equipment),
        },
        "hierarchy": hierarchy,
        "equipment": equipment,
    }

    logger.info(
        f"Parsed: {len(storeys)} storeys, {len(spaces)} spaces, {len(equipment)} equipment"
    )
    return result
