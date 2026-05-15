"""
Modèles Pydantic pour le IFC Parser Service
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SiteInfo(BaseModel):
    name: str
    global_id: str
    description: Optional[str] = ""


class BuildingInfo(BaseModel):
    name: str
    global_id: str
    description: Optional[str] = ""


class ProjectInfo(BaseModel):
    project_name: str
    global_id: str
    description: Optional[str] = ""
    sites: List[SiteInfo] = []
    buildings: List[BuildingInfo] = []


class StoreyInfo(BaseModel):
    global_id: str
    name: str
    elevation_m: Optional[float] = None
    description: Optional[str] = ""


class SpaceInfo(BaseModel):
    global_id: str
    name: str
    long_name: Optional[str] = ""
    description: Optional[str] = ""
    storey: Optional[Dict[str, str]] = None
    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    property_sets: Optional[Dict[str, Any]] = {}


class EquipmentInfo(BaseModel):
    ifc_type: str
    global_id: str
    name: str
    description: Optional[str] = ""
    property_sets: Optional[Dict[str, Any]] = {}


class LevelWithSpaces(StoreyInfo):
    spaces: List[SpaceInfo] = []


class Hierarchy(BaseModel):
    project: ProjectInfo
    levels: List[LevelWithSpaces] = []
    unassigned_spaces: Optional[List[SpaceInfo]] = []


class IFCSummary(BaseModel):
    storeys: int
    spaces: int
    equipment: int


class IFCParseResult(BaseModel):
    ifc_file: str
    schema: str
    summary: IFCSummary
    hierarchy: Hierarchy
    equipment: List[EquipmentInfo] = []


class ErrorResponse(BaseModel):
    detail: str
    code: str