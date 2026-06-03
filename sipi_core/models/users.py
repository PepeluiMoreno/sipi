from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, metadata, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoMixin


# Tabla de asociación muchos-a-muchos
usuario_rol = Table(
    "usuario_rol",
    metadata,
    Column("usuario_id", String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), primary_key=True),
    Column("rol_id", String(36), ForeignKey(f"{APP_SCHEMA}.roles.id"), primary_key=True),
    Column(
        "fecha_asignacion",
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    ),
    Column(
        "asignado_por",
        String(36),
        ForeignKey(f"{APP_SCHEMA}.usuarios.id"),
        nullable=True,
    ),
)


class Usuario(UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoMixin, Base):
    __tablename__ = "usuarios"

    nombre_usuario: Mapped[str] = mapped_column(String(100))
    hashed_contrasena: Mapped[str] = mapped_column(Text)
    email_verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    # Usuarios de sistema (etluser, admin_seed…) — protegidos contra borrado
    is_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list["Rol"]] = relationship(
        "Rol",
        secondary=usuario_rol,
        primaryjoin=lambda: Usuario.id == usuario_rol.c.usuario_id,
        secondaryjoin=lambda: Rol.id == usuario_rol.c.rol_id,
        back_populates="usuarios",
    )


class Rol(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "roles"

    nombre: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario",
        secondary=usuario_rol,
        primaryjoin=lambda: Rol.id == usuario_rol.c.rol_id,
        secondaryjoin=lambda: Usuario.id == usuario_rol.c.usuario_id,
        back_populates="roles",
    )
