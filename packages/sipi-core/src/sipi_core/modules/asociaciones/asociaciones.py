"""Asociaciones que usan SIPI.

Una **Asociacion** es una organización con acceso a la aplicación; agrupa a sus
usuarios. En SIPI un miembro de una asociación registrado **es** un usuario: no hay
entidad Miembro separada — el `Usuario` lleva su `asociacion_id` y `cargo`.

Usuarios regulares → pertenecen a una asociación. Usuarios especiales (superadmin,
sistema) → `asociacion_id` NULL + `is_sistema`.
"""
from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, ContactoMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Usuario


class Asociacion(UUIDPKMixin, AuditMixin, ContactoMixin, Base):
    """Organización con acceso a la aplicación. Agrupa a sus usuarios."""
    __tablename__ = "asociaciones"

    nombre: Mapped[str] = mapped_column(String(255), index=True)
    siglas: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    cif: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Ámbito territorial: área en que opera la asociación (acota los territorios de
    # los roles de sus usuarios). La FK más profunda no nula define el nivel; todas
    # nulas = ámbito nacional.
    ambito_comunidad_autonoma_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.comunidades_autonomas.id"), index=True)
    ambito_provincia_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.provincias.id"), index=True)
    ambito_municipio_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.municipios.id"), index=True)

    # foreign_keys explícito: AuditMixin añade FKs Asociacion→usuarios (created_by…),
    # así que el join de "usuarios de la asociación" debe usar Usuario.asociacion_id.
    usuarios: Mapped[List["Usuario"]] = relationship(
        "Usuario", foreign_keys="Usuario.asociacion_id", back_populates="asociacion")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Asociacion {self.siglas or self.nombre}>"
