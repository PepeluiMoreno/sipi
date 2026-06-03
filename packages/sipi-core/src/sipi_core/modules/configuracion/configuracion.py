# modules/configuracion/configuracion.py
from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import strawberry

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Usuario


@strawberry.enum
class TipoDato(str, enum.Enum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"


@strawberry.enum
class AmbitoConfig(str, enum.Enum):
    GLOBAL = "global"   # compartido por todo el sistema
    SIPI = "sipi"       # app de expedientes
    SURVEY = "survey"   # app de vigilancia


class Configuracion(UUIDPKMixin, AuditMixin, Base):
    """Parámetro tipado del sistema (clave única por ámbito)."""
    __tablename__ = "configuraciones"
    __table_args__ = (
        UniqueConstraint("clave", "ambito", name="uq_config_clave_ambito"),
    )

    clave: Mapped[str] = mapped_column(String(150), index=True, nullable=False,
                                       comment="p. ej. 'survey.idealista.intervalo_min'")
    valor: Mapped[Optional[str]] = mapped_column(Text, comment="Valor serializado como texto")
    tipo_dato: Mapped[TipoDato] = mapped_column(
        SQLEnum(TipoDato, name="tipo_dato_config", values_callable=lambda x: [e.value for e in x]),
        default=TipoDato.STR, nullable=False,
    )
    ambito: Mapped[AmbitoConfig] = mapped_column(
        SQLEnum(AmbitoConfig, name="ambito_config", values_callable=lambda x: [e.value for e in x]),
        default=AmbitoConfig.GLOBAL, index=True, nullable=False,
    )
    categoria: Mapped[Optional[str]] = mapped_column(String(80), index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    historial: Mapped[list["HistorialConfiguracion"]] = relationship(
        "HistorialConfiguracion", back_populates="configuracion", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Configuracion {self.ambito}:{self.clave}={self.valor!r}>"


class HistorialConfiguracion(UUIDPKMixin, Base):
    """Traza de cambios de un parámetro."""
    __tablename__ = "historial_configuracion"

    configuracion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.configuraciones.id", ondelete="CASCADE"), index=True)
    valor_anterior: Mapped[Optional[str]] = mapped_column(Text)
    valor_nuevo: Mapped[Optional[str]] = mapped_column(Text)
    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    configuracion: Mapped["Configuracion"] = relationship("Configuracion", back_populates="historial")
