"""Entidad territorial recursiva — modelo único para toda la jerarquía territorial.

Unifica en una sola tabla auto-referente (adjacency list) los dos árboles de SIPI:
  - **administrativo**: comunidad_autonoma → provincia → municipio → entidad_local_menor
                        (+ concejo, comarca… sin tocar el modelo)
  - **eclesiastico**:   provincia_eclesiastica → diocesis → parroquia

`tipo` es libre (string) para soportar niveles peculiares; `dominio` discrimina el árbol.
La ubicación legible de un inmueble se calcula subiendo por `parent_id` (máx. 3 niveles),
con el nombre del nivel dinámico desde `tipo`.

Fase 1 (strangler): se puebla por ETL desde las 7 tablas originales, que se conservan
(`origen_tabla`/`origen_id` mantienen la trazabilidad). El cutover de consumidores es posterior.
"""
from __future__ import annotations

from typing import Optional, List

from sqlalchemy import String, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin


class EntidadTerritorial(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "entidades_territoriales"
    __table_args__ = (
        Index("ix_entidad_territorial_origen", "origen_tabla", "origen_id"),
    )

    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.entidades_territoriales.id", ondelete="SET NULL"), index=True)

    dominio: Mapped[str] = mapped_column(String(40), index=True, nullable=False,
                                         comment="administrativo | eclesiastico | …")
    tipo: Mapped[str] = mapped_column(String(50), index=True, nullable=False,
                                      comment="comunidad_autonoma|provincia|municipio|entidad_local_menor|"
                                              "provincia_eclesiastica|diocesis|parroquia|concejo|comarca…")
    nombre: Mapped[str] = mapped_column(String(300), index=True, nullable=False)
    codigo: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    latitud: Mapped[Optional[float]] = mapped_column(Float)
    longitud: Mapped[Optional[float]] = mapped_column(Float)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Trazabilidad del ETL desde las tablas originales (Fase 1).
    origen_tabla: Mapped[Optional[str]] = mapped_column(String(50))
    origen_id: Mapped[Optional[str]] = mapped_column(String(36))

    parent: Mapped[Optional["EntidadTerritorial"]] = relationship(
        "EntidadTerritorial", remote_side="EntidadTerritorial.id", back_populates="hijos")
    hijos: Mapped[List["EntidadTerritorial"]] = relationship(
        "EntidadTerritorial", back_populates="parent")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EntidadTerritorial {self.tipo}:{self.nombre!r}>"
