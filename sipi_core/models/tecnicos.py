
# models/actores/tecnicos.py
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoDireccionMixin

if TYPE_CHECKING:
    from sipi_core.models.geografia import Municipio
    from sipi_core.models.inmuebles import IntervencionTecnico
    from sipi_core.models.tipologias import TipoRolTecnico

class Tecnico(UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoDireccionMixin, Base):
    __tablename__ = "tecnicos"

    rol_tecnico_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.roles_tecnico.id"),
        index=True,
    )
    colegio_profesional_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.colegios_profesionales.id"),
        index=True,
    )
    numero_colegiado: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    fecha_colegiacion: Mapped[Optional[datetime]] = mapped_column()

    rol_tecnico: Mapped[Optional["TipoRolTecnico"]] = relationship(
        "TipoRolTecnico", back_populates="tecnicos"
    )
    colegio_profesional: Mapped[Optional["ColegioProfesional"]] = relationship(
        "ColegioProfesional", back_populates="tecnicos"
    )
    municipio_trabajo: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(Tecnico.municipio_id) == Municipio.id",
        back_populates="tecnicos",
    )
    intervenciones: Mapped[list["IntervencionTecnico"]] = relationship(
        "IntervencionTecnico", back_populates="tecnico"
    )

    def __repr__(self) -> str:
        return f"<Tecnico {self.numero_colegiado} - {self.nombre}>"


class ColegioProfesional(UUIDPKMixin, AuditMixin, ContactoDireccionMixin, Base):
    __tablename__ = "colegios_profesionales"

    nombre: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    codigo: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)

    municipio_sede: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(ColegioProfesional.municipio_id) == Municipio.id",
        back_populates="colegios_profesionales",
    )
    tecnicos: Mapped[list["Tecnico"]] = relationship(
        "Tecnico", back_populates="colegio_profesional"
    )

    def __repr__(self) -> str:
        return f"<ColegioProfesional {self.codigo} - {self.nombre}>"
