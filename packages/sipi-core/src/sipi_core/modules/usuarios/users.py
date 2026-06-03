from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

import enum
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Table,
    Column,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import strawberry

from sipi_core.db.registry import Base, metadata, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoMixin

if TYPE_CHECKING:
    from sipi_core.modules.acceso.permisos import RolTransaccion, RolFuncionalidad


@strawberry.enum
class TipoRol(str, enum.Enum):
    SISTEMA = "sistema"          # roles internos (admin, etluser…)
    FUNCIONAL = "funcional"      # roles de negocio (catalogador, validador…)
    TERRITORIAL = "territorial"  # roles con ámbito geográfico


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

    # --- RBAC (estilo SIGA), aditivo ---
    codigo: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True,
                                                  comment="Código estable del rol, p. ej. 'validador'")
    tipo: Mapped[TipoRol] = mapped_column(
        SQLEnum(TipoRol, name="tipo_rol", values_callable=lambda x: [e.value for e in x]),
        default=TipoRol.FUNCIONAL, nullable=False,
    )
    nivel: Mapped[int] = mapped_column(Integer, default=0, nullable=False,
                                       comment="Jerarquía (mayor = más privilegio)")
    es_territorial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nivel_territorial: Mapped[Optional[str]] = mapped_column(
        String(50), comment="comunidad_autonoma | provincia | municipio (si es_territorial)")
    sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,
                                          comment="Rol del sistema, protegido")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario",
        secondary=usuario_rol,
        primaryjoin=lambda: Rol.id == usuario_rol.c.rol_id,
        secondaryjoin=lambda: Usuario.id == usuario_rol.c.usuario_id,
        back_populates="roles",
    )
    transacciones: Mapped[List["RolTransaccion"]] = relationship(
        "RolTransaccion", back_populates="rol", cascade="all, delete-orphan")
    funcionalidades: Mapped[List["RolFuncionalidad"]] = relationship(
        "RolFuncionalidad", back_populates="rol", cascade="all, delete-orphan")
