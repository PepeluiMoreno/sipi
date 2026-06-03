# models/expedientes.py
"""
Hallazgo y Expediente.

Flujo de dominio (corregido):
  1. Los watchers/vigilantes de cada fuente extraen datos → se registran como
     `Hallazgo` (estado PENDIENTE, con scoring `certeza`/`confianza`).
  2. El humano COMPRUEBA el hallazgo (transacción RBAC `hallazgo.verificar`):
     VERIFICADO o DESCARTADO.
  3. Un hallazgo VERIFICADO se incorpora a un `Expediente` existente del inmueble
     o ABRE uno nuevo.

`Expediente` = dosier del inmueble (estado de ciclo de vida + bitácora de
hallazgos comprobados). El flujo de validación y el scoring viven en `Hallazgo`,
NO en el expediente.
"""
from __future__ import annotations
import enum
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Numeric, Boolean, ForeignKey, Date, DateTime, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
import strawberry

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.inmuebles.inmuebles import Inmueble
    from sipi_core.modules.usuarios.users import Usuario


@strawberry.enum
class EstadoCicloVida(str, enum.Enum):
    """Estado actual del inmueble en su ciclo de vida."""
    INMATRICULADO = "inmatriculado"
    EN_VENTA = "en_venta"
    VENDIDO = "vendido"
    CAMBIO_DE_USO = "cambio_de_uso"
    REHABILITACION = "rehabilitacion"


@strawberry.enum
class GeoQuality(str, enum.Enum):
    """Calidad/origen de la geolocalización del inmueble."""
    MANUAL = "manual"
    AUTO = "auto"
    MISSING = "missing"


@strawberry.enum
class TipoEventoExpediente(str, enum.Enum):
    """Tipo de evento del ciclo de vida (de un hallazgo / entrada de expediente)."""
    ALTA_INMATRICULACION = "alta_inmatriculacion"
    PUESTA_EN_VENTA = "puesta_en_venta"
    VENDIDO = "vendido"
    CAMBIO_DE_USO = "cambio_de_uso"
    REHABILITACION = "rehabilitacion"
    REHABILITACION_SUBVENCIONADA = "rehabilitacion_subvencionada"
    DECLARACION_BIC = "declaracion_bic"
    CAMBIO_VISITABILIDAD = "cambio_visitabilidad"


@strawberry.enum
class EstadoHallazgo(str, enum.Enum):
    """Estado de comprobación del hallazgo (dato extraído por un watcher)."""
    PENDIENTE = "pendiente"      # extraído, pendiente de comprobar por un humano
    VERIFICADO = "verificado"    # comprobado → incorporado/abre Expediente
    DESCARTADO = "descartado"    # rechazado en la comprobación


@strawberry.enum
class CertezaHallazgo(str, enum.Enum):
    """Confianza del hallazgo (resultado del scoring; ver §2bis del diseño)."""
    CIERTO = "cierto"   # alta confianza → auto-verificable según umbral (configuracion)
    DUDOSO = "dudoso"   # baja confianza → comprobación humana


@strawberry.enum
class TipoExpediente(str, enum.Enum):
    """Asunto/tipo de un expediente (dosier) del inmueble. Cada expediente tiene
    sus propios datos (`datos`) y sus documentos colgados."""
    CATASTRAL = "catastral"            # información catastral (RC, uso, superficie…)
    ENAJENACION = "enajenacion"        # venta/transmisión
    INMATRICULACION = "inmatriculacion"
    PROTECCION = "proteccion"          # BIC/figuras de protección
    INTERVENCION = "intervencion"      # obras/rehabilitación
    HISTORICO = "historico"            # historiografía/bibliografía
    OTRO = "otro"


@strawberry.enum
class FuenteCoordenadas(str, enum.Enum):
    """Origen de las coordenadas del inmueble. Jerarquía de calidad para la
    idempotencia: MANUAL > OSM/WIKIDATA > CATASTRO > GEOCODER."""
    MANUAL = "manual"
    OSM = "osm"
    WIKIDATA = "wikidata"
    CATASTRO = "catastro"
    GEOCODER = "geocoder"


class Expediente(UUIDPKMixin, AuditMixin, Base):
    """Dosier de un inmueble: su estado de ciclo de vida + bitácora de hallazgos
    comprobados. Se abre cuando se verifica el primer hallazgo, o manualmente."""
    __tablename__ = "expedientes"

    inmueble_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.inmuebles.id", ondelete="CASCADE"),
        index=True, nullable=False,
        comment="Inmueble del que este expediente es el dosier",
    )
    # Asunto del dosier: cada expediente es de un tipo (catastral, enajenación…)
    tipo: Mapped[TipoExpediente] = mapped_column(
        SQLEnum(TipoExpediente, name="tipo_expediente",
                values_callable=lambda x: [e.value for e in x]),
        default=TipoExpediente.OTRO, index=True, nullable=False,
    )
    titulo: Mapped[Optional[str]] = mapped_column(String(255))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    # Datos específicos del tipo de expediente (catastral: RC/uso/sup.; enajenación:
    # comprador/precio/fecha/notaría; etc.). Esquema flexible por tipo.
    datos: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Estado de ciclo de vida — relevante sobre todo para el dosier de inmatriculación;
    # nullable porque un dosier catastral/enajenación no tiene "ciclo de vida" propio.
    estado_actual: Mapped[Optional[EstadoCicloVida]] = mapped_column(
        SQLEnum(EstadoCicloVida, name="estado_ciclo_vida",
                values_callable=lambda x: [e.value for e in x], create_type=False),
        index=True, nullable=True,
        comment="Estado de ciclo de vida vigente (dosier de inmatriculación)",
    )
    fecha_apertura: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)
    abierto_por_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), index=True, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    inmueble: Mapped["Inmueble"] = relationship(
        "Inmueble", back_populates="expedientes", foreign_keys=[inmueble_id])
    abierto_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[abierto_por_id], viewonly=True)
    hallazgos: Mapped[List["Hallazgo"]] = relationship(
        "Hallazgo", back_populates="expediente", foreign_keys="Hallazgo.expediente_id")
    # Documentos colgados de este expediente (vía InmuebleDocumento.expediente_id)
    documentos: Mapped[List["InmuebleDocumento"]] = relationship(
        "InmuebleDocumento", back_populates="expediente",
        foreign_keys="InmuebleDocumento.expediente_id")

    def __repr__(self) -> str:
        return f"<Expediente {self.tipo} inmueble={self.inmueble_id}>"


class Hallazgo(UUIDPKMixin, AuditMixin, Base):
    """Dato extraído por un watcher/vigilante de una fuente, pendiente de
    comprobación humana. Unifica las detecciones de las distintas fuentes
    (portales, ODMGR/datasets, OSM…). Al verificarse, abre o engrosa un Expediente."""
    __tablename__ = "hallazgos"

    fuente: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False,
        comment="Watcher/fuente: 'idealista', 'fotocasa', 'odmgr:bdns', 'osm', 'manual'…")
    tipo_evento: Mapped[TipoEventoExpediente] = mapped_column(
        SQLEnum(TipoEventoExpediente, name="tipo_evento_expediente",
                values_callable=lambda x: [e.value for e in x]),
        index=True, nullable=False)
    estado: Mapped[EstadoHallazgo] = mapped_column(
        SQLEnum(EstadoHallazgo, name="estado_hallazgo",
                values_callable=lambda x: [e.value for e in x]),
        default=EstadoHallazgo.PENDIENTE, index=True, nullable=False)

    # Scoring (lo asigna el pipeline de descubrimiento)
    certeza: Mapped[Optional[CertezaHallazgo]] = mapped_column(
        SQLEnum(CertezaHallazgo, name="certeza_hallazgo",
                values_callable=lambda x: [e.value for e in x]),
        index=True, nullable=True)
    confianza: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))

    titulo: Mapped[Optional[str]] = mapped_column(String(255))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    datos: Mapped[Optional[dict]] = mapped_column(JSONB, comment="Datos crudos extraídos")
    url_evidencia: Mapped[Optional[str]] = mapped_column(String(500))
    fecha_evento: Mapped[Optional[date]] = mapped_column(Date, index=True)
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Inmueble candidato (puede no estar confirmado aún)
    inmueble_candidato_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.inmuebles.id"), index=True, nullable=True)
    # Origen polimórfico: la detección de la fuente (DeteccionAnuncio / OdmgrNotificationChange / InmuebleRaw)
    origen_tipo: Mapped[Optional[str]] = mapped_column(String(50))
    origen_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)

    # Comprobación humana (transacción RBAC hallazgo.verificar/descartar)
    verificado_por_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), index=True, nullable=True)
    verificado_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Expediente al que se incorpora al verificarse (NULL mientras pendiente)
    expediente_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.expedientes.id", ondelete="SET NULL"),
        index=True, nullable=True)

    inmueble_candidato: Mapped[Optional["Inmueble"]] = relationship(
        "Inmueble", foreign_keys=[inmueble_candidato_id], viewonly=True)
    verificado_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[verificado_por_id], viewonly=True)
    expediente: Mapped[Optional["Expediente"]] = relationship(
        "Expediente", back_populates="hallazgos", foreign_keys=[expediente_id])

    __table_args__ = (
        Index("ix_hallazgos_estado_certeza", "estado", "certeza"),
        Index("ix_hallazgos_inmueble_candidato", "inmueble_candidato_id"),
    )

    @property
    def es_pendiente(self) -> bool:
        return self.estado == EstadoHallazgo.PENDIENTE

    def __repr__(self) -> str:
        return f"<Hallazgo {self.fuente}:{self.tipo_evento} estado={self.estado}>"
