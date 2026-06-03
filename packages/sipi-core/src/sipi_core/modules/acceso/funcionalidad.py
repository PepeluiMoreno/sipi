# modules/acceso/funcionalidad.py
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.acceso.transaccion import Transaccion
    from sipi_core.modules.acceso.permisos import RolFuncionalidad


class Funcionalidad(UUIDPKMixin, AuditMixin, Base):
    """Agrupación de transacciones para la UI (una pantalla/feature)."""
    __tablename__ = "funcionalidades"

    codigo: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    modulo: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    transacciones: Mapped[List["FuncionalidadTransaccion"]] = relationship(
        "FuncionalidadTransaccion", back_populates="funcionalidad", cascade="all, delete-orphan")
    roles: Mapped[List["RolFuncionalidad"]] = relationship(
        "RolFuncionalidad", back_populates="funcionalidad", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Funcionalidad {self.codigo}>"


class FuncionalidadTransaccion(UUIDPKMixin, Base):
    """Pivot funcionalidad ↔ transacción."""
    __tablename__ = "funcionalidades_transacciones"
    __table_args__ = (
        UniqueConstraint("funcionalidad_id", "transaccion_id", name="uq_func_transaccion"),
    )

    funcionalidad_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.funcionalidades.id", ondelete="CASCADE"), index=True)
    transaccion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.transacciones.id", ondelete="CASCADE"), index=True)

    funcionalidad: Mapped["Funcionalidad"] = relationship("Funcionalidad", back_populates="transacciones")
    transaccion: Mapped["Transaccion"] = relationship("Transaccion", back_populates="funcionalidades")
