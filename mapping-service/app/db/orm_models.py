"""
Modèles SQLAlchemy (tables PostgreSQL)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class SpaceMapping(Base):
    """
    Table principale : une ligne = une salle IFC mappée à 0..N capteurs.
    """
    __tablename__ = "space_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Côté IFC ──────────────────────────────
    space_global_id = Column(String(64), unique=True, nullable=False, index=True,
                             comment="GlobalId IFC de la salle")
    space_name = Column(String(255), nullable=False, comment="Nom de la salle (IFC Name)")
    space_long_name = Column(String(255), nullable=True, comment="LongName IFC")
    storey_name = Column(String(255), nullable=True, comment="Étage / BuildingStorey")
    area_m2 = Column(Float, nullable=True, comment="Surface en m²")

    # ── Métadonnées ───────────────────────────
    project_name = Column(String(255), nullable=True, comment="Nom du projet IFC")
    ifc_filename = Column(String(512), nullable=True, comment="Nom du fichier IFC source")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True, comment="Notes libres")

    # ── Relation vers les capteurs assignés ───
    sensors = relationship("SensorAssignment", back_populates="space_mapping",
                           cascade="all, delete-orphan")


class SensorAssignment(Base):
    """
    Table des capteurs assignés à une salle.
    Une salle peut avoir plusieurs capteurs de types différents.
    """
    __tablename__ = "sensor_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Clé étrangère vers la salle ──────────
    space_mapping_id = Column(Integer, ForeignKey("space_mappings.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    space_mapping = relationship("SpaceMapping", back_populates="sensors")

    # ── Côté WaveOn ──────────────────────────
    sensor_type = Column(String(32), nullable=False,
                         comment="'ble_node' ou 'smart_controller'")
    device_id = Column(String(64), nullable=True, comment="id_ble_node ou id_smart_controller")
    unicast = Column(String(32), nullable=True, comment="Adresse unicast (hex ou dec)")
    device_name = Column(String(255), nullable=True, comment="Nom du capteur WaveOn")
    network_id = Column(Integer, nullable=True, comment="idNetwork WaveOn")
    pid_label = Column(String(128), nullable=True, comment="Type de capteur (présence, temp...)")
    sensor_types_str = Column(String(512), nullable=True,
                              comment="Types de mesure séparés par virgule")

    # ── Métadonnées ───────────────────────────
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
