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
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import strawberry

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoMixin

if TYPE_CHECKING:
    from sipi_core.modules.acceso.permisos import RolTransaccion, RolFuncionalidad
    from sipi_core.modules.asociaciones.asociaciones import Asociacion


@strawberry.enum
class TipoRol(str, enum.Enum):
    SISTEMA = "sistema"          # roles internos (admin, etluser…)
    FUNCIONAL = "funcional"      # roles de negocio (catalogador, validador…)
    TERRITORIAL = "territorial"  # roles con ámbito geográfico


class Usuario(UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoMixin, Base):
    __tablename__ = "usuarios"

    nombre_usuario: Mapped[str] = mapped_column(String(100))
    hashed_contrasena: Mapped[str] = mapped_column(Text)
    email_verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    # Usuarios de sistema (etluser, admin_seed…) — protegidos contra borrado
    is_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Consentimiento para recibir notificaciones de eventos de la aplicación
    acepta_notificaciones: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # En SIPI el usuario ES el miembro de una asociación. `asociacion_id` puesto →
    # usuario regular; NULL → usuario especial (superadmin/sistema, con is_sistema).
    asociacion_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.asociaciones.id", ondelete="SET NULL"),
        index=True, nullable=True)
    cargo: Mapped[Optional[str]] = mapped_column(String(100), comment="Cargo en la asociación")
    asociacion: Mapped[Optional["Asociacion"]] = relationship(
        "Asociacion", foreign_keys=[asociacion_id], back_populates="usuarios")

    # Asignaciones (objeto-asociación; escritura vía UsuarioRol / createUsuarioRol)
    roles_asignados: Mapped[List["UsuarioRol"]] = relationship(
        "UsuarioRol", foreign_keys="UsuarioRol.usuario_id",
        back_populates="usuario", cascade="all, delete-orphan")
    # Acceso de solo lectura a los roles (lo usan authz / matriz de permisos)
    roles: Mapped[list["Rol"]] = relationship(
        "Rol", secondary=lambda: UsuarioRol.__table__,
        primaryjoin="Usuario.id == UsuarioRol.usuario_id",
        secondaryjoin="Rol.id == UsuarioRol.rol_id",
        viewonly=True, back_populates="usuarios")


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

    usuarios_asignados: Mapped[List["UsuarioRol"]] = relationship(
        "UsuarioRol", foreign_keys="UsuarioRol.rol_id",
        back_populates="rol", cascade="all, delete-orphan")
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", secondary=lambda: UsuarioRol.__table__,
        primaryjoin="Rol.id == UsuarioRol.rol_id",
        secondaryjoin="Usuario.id == UsuarioRol.usuario_id",
        viewonly=True, back_populates="roles")
    transacciones: Mapped[List["RolTransaccion"]] = relationship(
        "RolTransaccion", back_populates="rol", cascade="all, delete-orphan")
    funcionalidades: Mapped[List["RolFuncionalidad"]] = relationship(
        "RolFuncionalidad", back_populates="rol", cascade="all, delete-orphan")


class UsuarioRol(UUIDPKMixin, Base):
    """Asignación usuario↔rol (objeto-asociación, expuesto en GraphQL).
    Sustituye a la antigua tabla de asociación `usuario_rol`."""
    __tablename__ = "usuario_rol"
    __table_args__ = (
        UniqueConstraint("usuario_id", "rol_id", name="uq_usuario_rol"),
    )

    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id", ondelete="CASCADE"), index=True)
    rol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.roles.id", ondelete="CASCADE"), index=True)
    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    asignado_por: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), nullable=True)

    # Territorio del rol (para roles territoriales). Acotado por el ámbito de la
    # asociación del usuario. La FK más profunda no nula define el nivel.
    comunidad_autonoma_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.comunidades_autonomas.id"), index=True)
    provincia_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.provincias.id"), index=True)
    municipio_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.municipios.id"), index=True)

    usuario: Mapped["Usuario"] = relationship(
        "Usuario", foreign_keys=[usuario_id], back_populates="roles_asignados")
    rol: Mapped["Rol"] = relationship(
        "Rol", foreign_keys=[rol_id], back_populates="usuarios_asignados")
