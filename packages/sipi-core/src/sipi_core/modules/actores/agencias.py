# models/agencias.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, ContactoDireccionMixin

if TYPE_CHECKING:
    from sipi_core.modules.geografia.geografia import Municipio, Provincia
    from sipi_core.modules.transmisiones.transmisiones import TransmisionAnunciante


class AgenciaInmobiliaria(UUIDPKMixin, AuditMixin, ContactoDireccionMixin, Base):
    __tablename__ = "agencias_inmobiliarias"
    __table_args__ = {"schema": APP_SCHEMA}

    nombre: Mapped[str] = mapped_column(String(255), index=True)

    # Identificador externo en Fotocasa (clientId). Único por cuenta Fotocasa;
    # una misma cadena puede tener varios si opera con delegaciones independientes.
    fotocasa_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)

    # Fuente de alta inicial: 'Fotocasa', 'RERA', 'manual', …
    fuente: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)

    # ── Relaciones ────────────────────────────────────────────────────────────

    municipio_oficina: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin=f"foreign(AgenciaInmobiliaria.municipio_id) == Municipio.id",
        back_populates="agencias_inmobiliarias",
    )

    presencia_provincial: Mapped[List["AgenciaProvincia"]] = relationship(
        "AgenciaProvincia",
        back_populates="agencia",
        cascade="all, delete-orphan",
    )

    transmisiones_anunciadas: Mapped[List["TransmisionAnunciante"]] = relationship(
        "TransmisionAnunciante",
        back_populates="agencia_inmobiliaria",
    )

    def __repr__(self) -> str:
        return f"<AgenciaInmobiliaria {self.nombre}>"


class AgenciaProvincia(Base):
    """
    Tabla pivot: presencia de una agencia en una provincia concreta.

    Una agencia (agency_id de Fotocasa) puede aparecer en N provincias.
    Para cada par (agencia, provincia, fuente) guardamos las métricas
    que provee la fuente (inmuebles, precio mínimo, URL de búsqueda).

    UNIQUE (agencia_id, provincia_id, fuente) → un único registro
    por agencia × provincia × fuente; se actualiza en cada ejecución ETL.
    """
    __tablename__ = "agencias_provincias"
    __table_args__ = (
        UniqueConstraint("agencia_id", "provincia_id", "fuente", name="uq_agencia_provincia_fuente"),
        {"schema": APP_SCHEMA},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    agencia_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.agencias_inmobiliarias.id", ondelete="CASCADE"),
        index=True,
    )
    provincia_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.provincias.id"),
        index=True,
    )

    # Fuente que origina el registro (Fotocasa, RERA, …)
    fuente: Mapped[str] = mapped_column(String(50))

    # Métricas de la fuente en esta provincia
    inmuebles_zona: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    inmuebles_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    precio_minimo: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    url_busqueda: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Auditoría ligera (sin created_by)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True,
    )

    # ── Relaciones ────────────────────────────────────────────────────────────

    agencia: Mapped["AgenciaInmobiliaria"] = relationship(
        "AgenciaInmobiliaria",
        back_populates="presencia_provincial",
    )

    provincia: Mapped["Provincia"] = relationship(
        "Provincia",
        primaryjoin=f"foreign(AgenciaProvincia.provincia_id) == Provincia.id",
    )

    def __repr__(self) -> str:
        return f"<AgenciaProvincia agencia={self.agencia_id} prov={self.provincia_id} fuente={self.fuente}>"
