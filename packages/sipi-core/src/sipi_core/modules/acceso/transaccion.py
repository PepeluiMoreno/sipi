# modules/acceso/transaccion.py
from __future__ import annotations
import enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import strawberry

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.acceso.permisos import RolTransaccion
    from sipi_core.modules.acceso.funcionalidad import FuncionalidadTransaccion


@strawberry.enum
class TipoTransaccion(str, enum.Enum):
    """Naturaleza de la acción (para UI/auditoría)."""
    CONSULTA = "consulta"      # lectura
    OPERACION = "operacion"    # escritura/acción de dominio
    ADMIN = "admin"            # administración del sistema


class Transaccion(UUIDPKMixin, AuditMixin, Base):
    """Acción atómica autorizable. p. ej. `hallazgo.verificar`, `inmueble.crear`."""
    __tablename__ = "transacciones"

    codigo: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False,
                                        comment="Código único, p. ej. 'expediente.ratificar'")
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    modulo: Mapped[str] = mapped_column(String(100), index=True, nullable=False,
                                        comment="Módulo/dominio al que pertenece (expediente, inmueble, vigilancia…)")
    tipo: Mapped[TipoTransaccion] = mapped_column(
        SQLEnum(TipoTransaccion, name="tipo_transaccion",
                values_callable=lambda x: [e.value for e in x]),
        default=TipoTransaccion.OPERACION, nullable=False,
    )
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    sistema: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False,
                                          comment="Transacción del sistema (no editable por el usuario)")

    roles: Mapped[List["RolTransaccion"]] = relationship(
        "RolTransaccion", back_populates="transaccion", cascade="all, delete-orphan")
    funcionalidades: Mapped[List["FuncionalidadTransaccion"]] = relationship(
        "FuncionalidadTransaccion", back_populates="transaccion", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Transaccion {self.codigo}>"
