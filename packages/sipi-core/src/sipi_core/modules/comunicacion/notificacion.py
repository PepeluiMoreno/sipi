# modules/comunicacion/notificacion.py
from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import strawberry

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Usuario


@strawberry.enum
class PrioridadNotif(str, enum.Enum):
    BAJA = "baja"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"


class TipoNotificacion(UUIDPKMixin, AuditMixin, Base):
    """Catálogo de tipos de notificación (plantilla + canales + prioridad)."""
    __tablename__ = "tipos_notificacion"

    codigo: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False,
                                        comment="p. ej. 'hallazgo.propuesto', 'expediente.ratificado'")
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    categoria: Mapped[str] = mapped_column(String(50), index=True, default="dominio")
    prioridad: Mapped[PrioridadNotif] = mapped_column(
        SQLEnum(PrioridadNotif, name="prioridad_notif", values_callable=lambda x: [e.value for e in x]),
        default=PrioridadNotif.NORMAL, nullable=False,
    )
    requiere_accion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permite_inapp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permite_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_asunto: Mapped[Optional[str]] = mapped_column(String(200))
    template_cuerpo: Mapped[Optional[str]] = mapped_column(Text)
    icono: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    notificaciones: Mapped[List["Notificacion"]] = relationship(
        "Notificacion", back_populates="tipo")

    def __repr__(self) -> str:
        return f"<TipoNotificacion {self.codigo}>"


class Notificacion(UUIDPKMixin, Base):
    """Instancia de notificación para un usuario."""
    __tablename__ = "notificaciones"

    tipo_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.tipos_notificacion.id"), index=True, nullable=False)
    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id", ondelete="CASCADE"), index=True, nullable=False)

    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    cuerpo: Mapped[Optional[str]] = mapped_column(Text)
    prioridad: Mapped[PrioridadNotif] = mapped_column(
        SQLEnum(PrioridadNotif, name="prioridad_notif", values_callable=lambda x: [e.value for e in x],
                create_type=False),
        default=PrioridadNotif.NORMAL, nullable=False,
    )
    accion_url: Mapped[Optional[str]] = mapped_column(String(500))
    # Vínculo polimórfico a la entidad de dominio (p. ej. Expediente)
    entidad_tipo: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    entidad_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)

    leida: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    leida_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    tipo: Mapped["TipoNotificacion"] = relationship("TipoNotificacion", back_populates="notificaciones")
    usuario: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[usuario_id])

    __table_args__ = (
        Index("ix_notif_usuario_leida", "usuario_id", "leida"),
    )
