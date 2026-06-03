# modules/acceso/permisos.py
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Rol
    from sipi_core.modules.acceso.transaccion import Transaccion
    from sipi_core.modules.acceso.funcionalidad import Funcionalidad


class RolTransaccion(UUIDPKMixin, AuditMixin, Base):
    """Pivot rol ↔ transacción: el permiso efectivo."""
    __tablename__ = "roles_transacciones"
    __table_args__ = (
        UniqueConstraint("rol_id", "transaccion_id", name="uq_rol_transaccion"),
    )

    rol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.roles.id", ondelete="CASCADE"), index=True)
    transaccion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.transacciones.id", ondelete="CASCADE"), index=True)

    rol: Mapped["Rol"] = relationship("Rol", back_populates="transacciones")
    transaccion: Mapped["Transaccion"] = relationship("Transaccion", back_populates="roles")


class RolFuncionalidad(UUIDPKMixin, AuditMixin, Base):
    """Pivot rol ↔ funcionalidad (visibilidad de pantallas en la UI)."""
    __tablename__ = "roles_funcionalidades"
    __table_args__ = (
        UniqueConstraint("rol_id", "funcionalidad_id", name="uq_rol_funcionalidad"),
    )

    rol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.roles.id", ondelete="CASCADE"), index=True)
    funcionalidad_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.funcionalidades.id", ondelete="CASCADE"), index=True)

    rol: Mapped["Rol"] = relationship("Rol", back_populates="funcionalidades")
    funcionalidad: Mapped["Funcionalidad"] = relationship("Funcionalidad", back_populates="roles")
