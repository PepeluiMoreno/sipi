
# models/documentos.py
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin, DocumentoMixin

if TYPE_CHECKING:
    from sipi_core.modules.inmuebles.inmuebles import Inmueble
    from sipi_core.modules.catalogos.tipologias import TipoDocumento, TipoLicencia
    from sipi_core.modules.documentos.documentos import FuenteDocumental
    from sipi_core.modules.expedientes.expedientes import Expediente


class Documento(UUIDPKMixin, AuditMixin, DocumentoMixin, Base):
    __tablename__ = "documentos"

    tipo_documento_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.tipos_documento.id", ondelete="RESTRICT"),
        index=True,
    )
    tipo_licencia_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.tipos_licencia.id", ondelete="RESTRICT"),
        index=True,
    )
    fuente_documental_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.fuentes_documentales.id", ondelete="RESTRICT"),
        index=True,
    )

    inmuebles: Mapped[list["InmuebleDocumento"]] = relationship(
        "InmuebleDocumento",
        back_populates="documento",
        cascade="all, delete-orphan",
    )
    tipo_documento: Mapped["TipoDocumento"] = relationship(
        "TipoDocumento",
        back_populates="documentos",
    )
    tipo_licencia: Mapped[Optional["TipoLicencia"]] = relationship(
        "TipoLicencia",
        back_populates="documentos",
    )
    fuente_documental: Mapped[Optional["FuenteDocumental"]] = relationship(
        "FuenteDocumental",
        back_populates="documentos",
    )


class InmuebleDocumento(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "inmuebles_documentos"

    inmueble_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.inmuebles.id", ondelete="CASCADE"),
        index=True,
    )
    documento_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.documentos.id", ondelete="CASCADE"),
        index=True,
    )
    # Expediente (dosier) al que se cuelga el documento. NULL = documento a nivel
    # de inmueble, sin asignar a un expediente concreto.
    expediente_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.expedientes.id", ondelete="SET NULL"),
        index=True, nullable=True,
    )
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    inmueble: Mapped["Inmueble"] = relationship(
        "Inmueble",
        back_populates="documentos",
    )
    documento: Mapped["Documento"] = relationship(
        "Documento",
        back_populates="inmuebles",
    )
    expediente: Mapped[Optional["Expediente"]] = relationship(
        "Expediente",
        back_populates="documentos",
        foreign_keys=[expediente_id],
    )
