# modules/comunicacion/vigilancia.py
"""Parametrización de procesos de vigilancia (survey offline).

Portado y adaptado desde la rama `feat/etl-odm-comunicacion` (que se escribió
sobre el layout antiguo). Aquí vive la CONFIGURACIÓN de cada proceso de
vigilancia: qué vigila, con qué frecuencia, con qué parámetros y quién recibe
sus avisos. El proceso survey la lee al planificar; no la inventa.

Se integra con el dominio local de comunicación: los avisos que emite un proceso
se materializan como `Notificacion` (con `proceso_id`), reutilizando el catálogo
tipado y la entrega/lectura por usuario ya existentes. No duplica esa tabla.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Usuario, Rol
    from sipi_core.modules.comunicacion.notificacion import Notificacion


# Vocabularios (String + valores documentados; sin tipos ENUM de PG)
TIPO_PROCESO = ("portal_inmobiliario", "desacralizacion", "subvenciones", "generico")
SEVERIDAD = ("info", "aviso", "alerta")


class ProcesoVigilancia(UUIDPKMixin, AuditMixin, Base):
    """Configuración de un proceso de vigilancia offline (survey).

    La parametrización vive aquí y se gestiona desde la vista de Configuración.
    El proceso survey la lee al arrancar/planificar; no la inventa.
    """
    __tablename__ = "procesos_vigilancia"

    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), index=True, nullable=False)  # TIPO_PROCESO
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Planificación
    frecuencia_cron: Mapped[Optional[str]] = mapped_column(String(100))  # p.ej. "0 */6 * * *"
    ultima_ejecucion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    proxima_ejecucion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Parámetros del proceso (regiones, keywords, portales, umbral_score, fuentes...)
    parametros: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Severidad por defecto de los avisos que emite
    severidad_defecto: Mapped[str] = mapped_column(String(10), default="aviso", nullable=False)

    destinatarios_roles: Mapped[List["ProcesoDestinatarioRol"]] = relationship(
        "ProcesoDestinatarioRol", back_populates="proceso", cascade="all, delete-orphan")
    destinatarios_usuarios: Mapped[List["ProcesoDestinatarioUsuario"]] = relationship(
        "ProcesoDestinatarioUsuario", back_populates="proceso", cascade="all, delete-orphan")
    # Avisos emitidos por este proceso (se materializan como Notificacion)
    notificaciones: Mapped[List["Notificacion"]] = relationship(
        "Notificacion", back_populates="proceso")

    def __repr__(self) -> str:
        return f"<ProcesoVigilancia {self.nombre} ({self.tipo})>"


class ProcesoDestinatarioRol(UUIDPKMixin, Base):
    """Destinatario de un proceso por rol (objeto-asociación, estilo UsuarioRol)."""
    __tablename__ = "proceso_destinatario_rol"
    __table_args__ = (
        UniqueConstraint("proceso_id", "rol_id", name="uq_proceso_destinatario_rol"),
    )

    proceso_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.procesos_vigilancia.id", ondelete="CASCADE"), index=True)
    rol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.roles.id", ondelete="CASCADE"), index=True)

    proceso: Mapped["ProcesoVigilancia"] = relationship(
        "ProcesoVigilancia", back_populates="destinatarios_roles")
    rol: Mapped["Rol"] = relationship("Rol", foreign_keys=[rol_id])


class ProcesoDestinatarioUsuario(UUIDPKMixin, Base):
    """Destinatario de un proceso por usuario concreto."""
    __tablename__ = "proceso_destinatario_usuario"
    __table_args__ = (
        UniqueConstraint("proceso_id", "usuario_id", name="uq_proceso_destinatario_usuario"),
    )

    proceso_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.procesos_vigilancia.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id", ondelete="CASCADE"), index=True)

    proceso: Mapped["ProcesoVigilancia"] = relationship(
        "ProcesoVigilancia", back_populates="destinatarios_usuarios")
    usuario: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[usuario_id])
