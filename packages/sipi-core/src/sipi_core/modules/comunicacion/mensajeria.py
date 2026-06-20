# modules/comunicacion/mensajeria.py
"""Mensajería usuario↔usuario por canales (net-nuevo).

Portado desde la rama `feat/etl-odm-comunicacion`. Es un eje DISTINTO de los
avisos de dominio (`Notificacion`): canales con miembros e hilos de mensajes.
No reutiliza la tabla de notificaciones (mismo criterio que el módulo de
comunicación de SIGA).
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Usuario


# Vocabularios (String + valores documentados)
TIPO_CANAL = ("directo", "grupo", "canal")
ROL_CANAL = ("admin", "miembro")
TIPO_MENSAJE = ("texto", "sistema")


class Canal(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "canales"

    nombre: Mapped[Optional[str]] = mapped_column(String(150))  # nulo en directos
    tipo: Mapped[str] = mapped_column(String(10), default="canal", nullable=False)  # TIPO_CANAL
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    privado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    miembros: Mapped[List["CanalMiembro"]] = relationship(
        "CanalMiembro", back_populates="canal", cascade="all, delete-orphan")
    mensajes: Mapped[List["Mensaje"]] = relationship(
        "Mensaje", back_populates="canal", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Canal {self.nombre or '(directo)'} ({self.tipo})>"


class CanalMiembro(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "canal_miembro"
    __table_args__ = (
        UniqueConstraint("canal_id", "usuario_id", name="uq_canal_miembro"),
    )

    canal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.canales.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id", ondelete="CASCADE"), index=True)
    rol_canal: Mapped[str] = mapped_column(String(10), default="miembro", nullable=False)  # ROL_CANAL
    # marca de última lectura -> permite calcular no leídos sin recibo por mensaje
    ultima_lectura_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notificar: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    canal: Mapped["Canal"] = relationship("Canal", back_populates="miembros")
    usuario: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[usuario_id])

    def __repr__(self) -> str:
        return f"<CanalMiembro canal={self.canal_id} user={self.usuario_id}>"


class Mensaje(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "mensajes"

    canal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.canales.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id", ondelete="SET NULL"), index=True)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), default="texto", nullable=False)  # TIPO_MENSAJE
    # hilos: respuesta a otro mensaje
    respuesta_a_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.mensajes.id", ondelete="SET NULL"), index=True)
    editado_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    canal: Mapped["Canal"] = relationship("Canal", back_populates="mensajes")
    autor: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[autor_id])

    def __repr__(self) -> str:
        return f"<Mensaje canal={self.canal_id} autor={self.autor_id}>"
