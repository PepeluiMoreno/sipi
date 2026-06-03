# models/expedientes.py
from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.models.inmuebles import Inmueble
    from sipi_core.models.documentos import Documento
    from sipi_core.models.historiografia import FuenteHistoriografica


class TipoExpediente(UUIDPKMixin, AuditMixin, Base):
    """Catálogo de tipos de expediente (episodios del ciclo de vida del inmueble).

    Dar de alta un tipo nuevo (p. ej. 'secularizacion', 'declaracion_ruina',
    'deteccion') es un alta en catálogo, NO una migración. `esquema_datos`
    describe (opcional) los campos esperados en el JSON `datos` del expediente,
    para validación en la capa de servicio.
    """
    __tablename__ = "tipos_expediente"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    # Si este tipo de expediente cambia el estado del ciclo de vida del inmueble,
    # a qué estado lo lleva (p. ej. secularizacion -> DESAFECTADO). Sirve para
    # derivar Inmueble.estado_actual.
    estado_resultante: Mapped[Optional[str]] = mapped_column(String(50))
    # Si los expedientes de este tipo deben generar notificación (p. ej. hallazgo,
    # enajenación, declaración de ruina).
    notificable: Mapped[bool] = mapped_column(Boolean, default=False)
    # Esquema (JSON) de los campos esperados en `Expediente.datos` para este tipo.
    esquema_datos: Mapped[Optional[dict]] = mapped_column(JSONB)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    expedientes: Mapped[List["Expediente"]] = relationship("Expediente", back_populates="tipo")


class Expediente(UUIDPKMixin, AuditMixin, Base):
    """Episodio del ciclo de vida de un inmueble.

    Modelo general que sustituye a las antiguas tablas-evento (inmatriculación,
    transmisión/enajenación, intervención, subvención, cambio de uso, nivel de
    protección, detección/hallazgo) y se extiende a cualquier otro tipo vía el
    catálogo `TipoExpediente`. El historial del inmueble es el conjunto de sus
    expedientes ordenados por fecha; `Inmueble.estado_actual` se deriva del
    último expediente relevante.
    """
    __tablename__ = "expedientes"

    inmueble_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.inmuebles.id"), index=True)
    tipo_expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.tipos_expediente.id"), index=True)

    # --- Campos comunes (columnas reales, indexables) ---
    fecha_inicio: Mapped[Optional[datetime]] = mapped_column(index=True)
    fecha_fin: Mapped[Optional[datetime]]
    estado: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # estado del propio expediente (borrador/confirmado/...)
    titulo: Mapped[Optional[str]] = mapped_column(String(255))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    importe: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))  # subvenciones, ventas...

    # --- Procedencia / referencia externa ---
    fuente_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("app.fuentes_historiograficas.id"), index=True)
    referencia_externa: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # decreto, código BDNS, RC catastral, finca registral...
    enlace: Mapped[Optional[str]] = mapped_column(String(500))
    confianza: Mapped[Optional[str]] = mapped_column(String(20))  # ALTA/MEDIA... (hallazgos y fusiones)

    # --- Carga específica del tipo (sin rigidez de esquema) ---
    datos: Mapped[Optional[dict]] = mapped_column(JSONB)

    # --- Relaciones ---
    inmueble: Mapped["Inmueble"] = relationship("Inmueble", back_populates="expedientes")
    tipo: Mapped["TipoExpediente"] = relationship("TipoExpediente", back_populates="expedientes")
    fuente: Mapped[Optional["FuenteHistoriografica"]] = relationship("FuenteHistoriografica")
    actores: Mapped[List["ExpedienteActor"]] = relationship(
        "ExpedienteActor", back_populates="expediente", cascade="all, delete-orphan")
    documentos: Mapped[List["ExpedienteDocumento"]] = relationship(
        "ExpedienteDocumento", back_populates="expediente", cascade="all, delete-orphan")


class ExpedienteActor(UUIDPKMixin, AuditMixin, Base):
    """Parte interviniente en un expediente y su rol.

    Referencia polimórfica al actor (mismo patrón que `Inmueble.propietario_*`):
    `tipo_actor` (código de TipoActor) + `actor_id` (UUID). El `rol` indica su
    papel en el expediente (titular, transmitente, adquiriente, técnico,
    administración concedente, diócesis, etc.).
    """
    __tablename__ = "expediente_actores"

    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.expedientes.id"), index=True)
    tipo_actor: Mapped[str] = mapped_column(String(50), index=True)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    rol: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    expediente: Mapped["Expediente"] = relationship("Expediente", back_populates="actores")


class ExpedienteDocumento(UUIDPKMixin, AuditMixin, Base):
    """Documento adjunto a un expediente."""
    __tablename__ = "expediente_documentos"

    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.expedientes.id"), index=True)
    documento_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.documentos.id"), index=True)

    expediente: Mapped["Expediente"] = relationship("Expediente", back_populates="documentos")
    documento: Mapped["Documento"] = relationship("Documento")
