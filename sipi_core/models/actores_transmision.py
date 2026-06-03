# models/actores_transmision.py
"""
Actores que intervienen en transmisiones patrimoniales.

Transmitente: quien vende / cede el inmueble.
Adquiriente:  quien lo adquiere.

Ambas tablas son registros planos con un discriminador polimórfico (tipo_actor)
que indica si el actor es una EntidadReligiosa, una Administracion o un Privado.
El campo actor_ref_id almacena el UUID del registro en la tabla de origen sin
constraint de FK (patrón polimórfico ya usado en Inmueble.propietario_actor_id).
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from db.registry import Base
from mixins import UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoDireccionMixin

if TYPE_CHECKING:
    from models.geografia import Municipio
    from models.transmisiones import Transmision

# Valores permitidos para tipo_actor
TIPO_ACTOR_ENTIDAD_RELIGIOSA = "entidad_religiosa"
TIPO_ACTOR_ADMINISTRACION = "administracion"
TIPO_ACTOR_PRIVADO = "privado"


class Transmitente(UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoDireccionMixin, Base):
    """
    Vendedor / cedente de un inmueble.

    tipo_actor: 'entidad_religiosa' | 'administracion' | 'privado'
    actor_ref_id: UUID del registro en la tabla correspondiente (sin FK)
    """
    __tablename__ = "transmitentes"

    tipo_actor: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    actor_ref_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)

    municipio_residencia: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(Transmitente.municipio_id) == Municipio.id",
    )
    transmisiones: Mapped[list["Transmision"]] = relationship(
        "Transmision",
        back_populates="transmitente",
        foreign_keys="Transmision.transmitente_id",
    )

    def __repr__(self) -> str:
        return f"<Transmitente [{self.tipo_actor}] {self.nombre}>"


class Adquiriente(UUIDPKMixin, AuditMixin, IdentificacionMixin, ContactoDireccionMixin, Base):
    """
    Comprador / adquiriente de un inmueble.

    tipo_actor: 'entidad_religiosa' | 'administracion' | 'privado'
    actor_ref_id: UUID del registro en la tabla correspondiente (sin FK)
    """
    __tablename__ = "adquirientes"

    tipo_actor: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    actor_ref_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)

    municipio_residencia: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(Adquiriente.municipio_id) == Municipio.id",
    )
    transmisiones: Mapped[list["Transmision"]] = relationship(
        "Transmision",
        back_populates="adquiriente",
        foreign_keys="Transmision.adquiriente_id",
    )

    def __repr__(self) -> str:
        return f"<Adquiriente [{self.tipo_actor}] {self.nombre}>"
