# models/actores/entidades_religiosas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, Text, Date, DateTime

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import (
    UUIDPKMixin,
    AuditMixin,
    IdentificacionMixin,
    ContactoDireccionMixin,
    TitularidadMixin,
)
from sipi_core.modules.actores.actores_base import TitularBase

if TYPE_CHECKING:
    from sipi_core.modules.geografia.geografia import Municipio
    from sipi_core.modules.inmuebles.inmuebles import Inmueble
    from sipi_core.modules.catalogos.tipologias import TipoEntidadReligiosa
    from sipi_core.modules.entidades_religiosas.entidades_religiosas import Parroquia


class ProvinciaEclesiastica(UUIDPKMixin, AuditMixin, Base):
    """
    Agrupación de diócesis bajo una archidiócesis metropolitana.
    13 provincias en España (CEE).

    FK circular: sede_metropolitana_id → diocesis.id
    Se resuelve en ETL en dos pasadas: primero diocesis, luego provincias.
    """
    __tablename__ = "provincias_eclesiasticas"

    nombre: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    wikidata_qid: Mapped[Optional[str]] = mapped_column(String(32), unique=True, index=True)

    # FK circular nullable hacia la archidiócesis que preside la provincia
    sede_metropolitana_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.diocesis.id"), nullable=True, index=True
    )

    sede_metropolitana: Mapped[Optional["Diocesis"]] = relationship(
        "Diocesis",
        foreign_keys="[ProvinciaEclesiastica.sede_metropolitana_id]",
        back_populates="provincia_como_sede",
    )
    diocesis: Mapped[list["Diocesis"]] = relationship(
        "Diocesis",
        foreign_keys="[Diocesis.provincia_eclesiastica_id]",
        back_populates="provincia_eclesiastica",
    )


class Diocesis(
    UUIDPKMixin,
    AuditMixin,
    ContactoDireccionMixin,
    TitularidadMixin,
    Base,
):
    __tablename__ = "diocesis"

    nombre: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    es_archidiocesis: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cee_slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    wikidata_qid: Mapped[Optional[str]] = mapped_column(String(32), unique=True, index=True)
    sitio_web_propio: Mapped[Optional[str]] = mapped_column(String(500))
    obispo_nombre: Mapped[Optional[str]] = mapped_column(String(200))
    obispo_foto_url: Mapped[Optional[str]] = mapped_column(String(500))

    # FK a provincia eclesiástica (nullable: se rellena en 2ª pasada del ETL)
    provincia_eclesiastica_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.provincias_eclesiasticas.id"), nullable=True, index=True
    )

    provincia_eclesiastica: Mapped[Optional["ProvinciaEclesiastica"]] = relationship(
        "ProvinciaEclesiastica",
        foreign_keys="[Diocesis.provincia_eclesiastica_id]",
        back_populates="diocesis",
    )
    # Relación inversa del FK circular de ProvinciaEclesiastica.sede_metropolitana_id
    provincia_como_sede: Mapped[Optional["ProvinciaEclesiastica"]] = relationship(
        "ProvinciaEclesiastica",
        foreign_keys="[ProvinciaEclesiastica.sede_metropolitana_id]",
        back_populates="sede_metropolitana",
        uselist=False,
    )
    municipio_sede: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(Diocesis.municipio_id) == Municipio.id",
        back_populates="diocesis",
    )
    parroquias: Mapped[list["Parroquia"]] = relationship(
        "Parroquia", back_populates="diocesis", cascade="all, delete-orphan"
    )
    entidades_religiosas: Mapped[list["EntidadReligiosa"]] = relationship(
        "EntidadReligiosa", back_populates="diocesis",
    )
    inmuebles: Mapped[list["Inmueble"]] = relationship(
        "Inmueble", back_populates="diocesis",
    )
    titulares: Mapped[list["DiocesisTitular"]] = relationship(
        "DiocesisTitular", back_populates="diocesis", cascade="all, delete-orphan",
    )


class DiocesisTitular(TitularBase, Base):
    __tablename__ = "diocesis_titulares"

    diocesis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.diocesis.id"),
        index=True,
    )

    diocesis: Mapped["Diocesis"] = relationship(
        "Diocesis",
        back_populates="titulares",
    )


class Parroquia(UUIDPKMixin, AuditMixin, Base):
    """
    Parroquia católica.

    Nodo de unión entre la jerarquía eclesiástica y la geográfica:
      - diocesis_id  → jerarquía católica
      - municipio_id → jerarquía geográfica INE (ComunidadAutonoma > Provincia > Municipio)
    """
    __tablename__ = "parroquias"

    nombre: Mapped[str] = mapped_column(String(255), index=True)
    # Advocación / titular de la iglesia (ej: "Nuestra Señora de la Asunción")
    titular: Mapped[Optional[str]] = mapped_column(String(255))

    # Jerarquía eclesiástica
    diocesis_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.diocesis.id"), nullable=True, index=True
    )
    # Jerarquía geográfica — punto de unión
    municipio_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.municipios.id"), nullable=True, index=True
    )

    # Contacto
    nombre_via: Mapped[Optional[str]] = mapped_column(String(255))
    codigo_postal: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20))

    # Trazabilidad ETL
    cee_url_diocesis: Mapped[Optional[str]] = mapped_column(String(500))

    diocesis: Mapped[Optional["Diocesis"]] = relationship(
        "Diocesis", back_populates="parroquias"
    )
    asociaciones_fieles: Mapped[list["EntidadReligiosa"]] = relationship(
        "EntidadReligiosa",
        foreign_keys="[EntidadReligiosa.parroquia_id]",
        back_populates="parroquia",
    )
    municipio: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(Parroquia.municipio_id) == Municipio.id",
        viewonly=True,
    )


class EntidadReligiosa(
    UUIDPKMixin,
    AuditMixin,
    IdentificacionMixin,
    ContactoDireccionMixin,
    TitularidadMixin,
    Base,
):
    __tablename__ = "entidades_religiosas"

    # ── Identificación RER ────────────────────────────────────────────────────
    numero_registro: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
    )
    # Número de registro anterior (cuando cambió el sistema de numeración)
    numero_registro_antiguo: Mapped[Optional[str]] = mapped_column(String(50))
    # Sección del RER: 'GENERAL' (entidades de cualquier confesión) o
    # 'ESPECIAL' (exclusivamente católicas: diócesis, parroquias, órdenes…)
    seccion: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    # Texto original del campo Sección tal como viene del RER
    seccion_rer: Mapped[Optional[str]] = mapped_column(String(50))
    # Confesión religiosa tal como figura en el RER:
    # 'CATÓLICOS', 'EVANGÉLICOS', 'ISLAM', 'JUDÍOS', 'BUDISTAS'…
    confesion: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    # NIF de la entidad (R-xxxxxxx para religiosas, G-xxxxxxxx para asociaciones)
    # Fuente: BDNS, BOE, o Catastro (datos protegidos — requiere acceso especial)
    nif: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    fecha_inscripcion_rer: Mapped[Optional[datetime]] = mapped_column()
    fecha_aprobacion_estatutos: Mapped[Optional[datetime]] = mapped_column()
    fecha_fundacion: Mapped[Optional[datetime]] = mapped_column()
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Territorialidad ───────────────────────────────────────────────────────
    # True → entidad ligada a un territorio (parroquia, diócesis, capellanía)
    # False → entidad que trasciende la división territorial (orden religiosa,
    #          congregación, federación, asociación de fieles…)
    es_territorial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Jerarquía eclesiástica (solo para entidades católicas territoriales) ──
    # Fuente primaria: campo "Diócesis" del detalle RER.
    # Fallback: inferencia por municipio_id si la entidad es ESPECIAL/CAT.
    diocesis_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.diocesis.id"), nullable=True, index=True,
    )

    # ── Jerarquía interna (órdenes → casas / provincias) ─────────────────────
    # El campo "Congregación y provincia" del RER identifica la congregación
    # madre. Se almacena el nombre original (parsear_congregacion) y se resuelve
    # nivel_superior_id en el script enriquecer_er_nivel_superior.py
    congregacion: Mapped[Optional[str]] = mapped_column(String(500))
    # INTERNACIONAL | ESTATAL | PROVINCIAL | LOCAL
    ambito_geografico: Mapped[Optional[str]] = mapped_column(String(20), index=True)

    # ── Tipología canónica (Derecho Canónico CIC 1983) ────────────────────────
    # tipo_canonico: posición en la jerarquía canónica
    #   INSTITUTO_VIDA_CONSAGRADA · SOCIEDAD_VIDA_APOSTOLICA · ASOCIACION_FIELES
    #   PRELATURA_PERSONAL · FUNDACION_PIA · DIOCESIS · PARROQUIA
    tipo_canonico: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    # subtipo: forma concreta dentro del tipo canónico
    #   ORDEN_RELIGIOSA · CONGREGACION · MONASTERIO · CONVENTO · CASA_RELIGIOSA
    #   COFRADIA · HERMANDAD · ARCHICOFRADIA · ASOCIACION_GENERICA
    subtipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    # parroquia_id: solo para ASOCIACION_FIELES de ámbito parroquial (cofradías, hermandades)
    parroquia_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.parroquias.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    nivel_superior_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.entidades_religiosas.id"), nullable=True, index=True,
    )
    nivel_superior: Mapped[Optional["EntidadReligiosa"]] = relationship(
        "EntidadReligiosa",
        remote_side="EntidadReligiosa.id",
        foreign_keys="EntidadReligiosa.nivel_superior_id",
        back_populates="entidades_subordinadas",
    )

    # ── Catastro OVC ──────────────────────────────────────────────────────────
    # Código natural de la Dirección General del Catastro (20 chars alfanumérico)
    # Permite identificar y cruzar el inmueble sede con datos catastrales
    referencia_catastral: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    # Uso catastral declarado: Religioso, Educativo, Cultural…
    uso_catastral: Mapped[Optional[str]] = mapped_column(String(100))

    # ── CONFER (Conferencia Española de Religiosos) ───────────────────────────
    # Nombre oficial tal como figura en el directorio CONFER (slug de matching)
    nombre_confer: Mapped[Optional[str]] = mapped_column(String(255))
    # True si la entidad está afiliada a CONFER según su directorio público
    afiliada_confer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ── Datos federativos (texto libre del RER) ───────────────────────────────
    # Para federaciones: lista de entidades federadas (texto tabular del RER)
    entidades_federadas: Mapped[Optional[str]] = mapped_column(Text)
    # Para cualquier entidad: federaciones a las que pertenece
    federaciones: Mapped[Optional[str]] = mapped_column(Text)
    # Lugares de culto declarados en el RER (texto con direcciones)
    lugares_culto: Mapped[Optional[str]] = mapped_column(Text)

    # ── Tipología ─────────────────────────────────────────────────────────────
    tipo_entidad_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.tipos_entidad_religiosa.id", ondelete="RESTRICT"), index=True,
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    parroquia: Mapped[Optional["Parroquia"]] = relationship(
        "Parroquia",
        foreign_keys=[parroquia_id],
        back_populates="asociaciones_fieles",
    )
    sedes: Mapped[list["Sede"]] = relationship(
        "Sede", back_populates="entidad_religiosa", cascade="all, delete-orphan",
    )
    tipo_entidad: Mapped[Optional["TipoEntidadReligiosa"]] = relationship(
        "TipoEntidadReligiosa",
        back_populates="entidades_religiosas",
    )
    diocesis: Mapped[Optional["Diocesis"]] = relationship(
        "Diocesis",
        back_populates="entidades_religiosas",
    )
    municipio_sede: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(EntidadReligiosa.municipio_id) == Municipio.id",
        back_populates="entidades_religiosas",
    )
    entidades_subordinadas: Mapped[list["EntidadReligiosa"]] = relationship(
        "EntidadReligiosa",
        foreign_keys="EntidadReligiosa.nivel_superior_id",
        back_populates="nivel_superior",
    )
    inmuebles: Mapped[list["Inmueble"]] = relationship(
        "Inmueble",
        back_populates="entidad_religiosa",
    )
    titulares: Mapped[list["EntidadReligiosaTitular"]] = relationship(
        "EntidadReligiosaTitular",
        back_populates="entidad_religiosa",
        cascade="all, delete-orphan",
    )
    subvenciones: Mapped[list["EntidadReligiosaSubvencion"]] = relationship(
        "EntidadReligiosaSubvencion",
        back_populates="entidad_religiosa",
        cascade="all, delete-orphan",
    )



class EntidadReligiosaSubvencion(UUIDPKMixin, AuditMixin, Base):
    """
    Concesión BDNS vinculada a una entidad religiosa.

    Fuente: Base de Datos Nacional de Subvenciones (infosubvenciones.es).
    Cada fila representa una concesión individual recibida por la entidad.

    El código natural de identificación es cod_concesion (ej: 'SB146548130'),
    único en la BDNS — se usa para idempotencia en cargas sucesivas.
    """
    __tablename__ = "subvenciones_entidades"

    entidad_religiosa_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.entidades_religiosas.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # ── Código natural BDNS ────────────────────────────────────────────────────
    # Identificador estable de la concesión (ej: 'SB146548130')
    cod_concesion: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    # id numérico interno BDNS — natural code para joins con otros datasets BDNS
    id_bdns: Mapped[Optional[int]] = mapped_column(index=True)
    # id numérico BDNS del beneficiario (idPersona) — permite agrupar concesiones
    id_persona_bdns: Mapped[Optional[int]] = mapped_column(index=True)

    # ── Datos económicos ───────────────────────────────────────────────────────
    fecha_concesion: Mapped[Optional[datetime]] = mapped_column()
    fecha_alta_bdns: Mapped[Optional[datetime]] = mapped_column()
    importe: Mapped[Optional[float]] = mapped_column()
    ayuda_equivalente: Mapped[Optional[float]] = mapped_column()

    # ── Tipo y descripción ─────────────────────────────────────────────────────
    # Tipo de instrumento: 'SUBVENCIÓN', 'BECA', 'PRÉSTAMO REEMBOLSABLE'…
    instrumento: Mapped[Optional[str]] = mapped_column(String(200))
    # Beneficiario raw tal como viene de BDNS (NIF + nombre)
    beneficiario_bdns: Mapped[Optional[str]] = mapped_column(String(500))

    # ── Convocatoria ───────────────────────────────────────────────────────────
    id_convocatoria_bdns: Mapped[Optional[int]] = mapped_column(index=True)
    numero_convocatoria: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    convocatoria: Mapped[Optional[str]] = mapped_column(String(500))
    # Descripción en lengua cooficial (catalán, euskera, gallego…)
    descripcion_cooficial: Mapped[Optional[str]] = mapped_column(String(500))
    tiene_proyecto: Mapped[Optional[bool]] = mapped_column()
    # Código INVENTE (sistema de inventario de la IGAE)
    codigo_invente: Mapped[Optional[str]] = mapped_column(String(50))

    # ── Nivel administrativo del organismo concedente ─────────────────────────
    nivel1: Mapped[Optional[str]] = mapped_column(String(50))   # LOCAL / AUTONÓMICO / ESTATAL / UE
    nivel2: Mapped[Optional[str]] = mapped_column(String(200))  # Nombre CCAA o Administración
    nivel3: Mapped[Optional[str]] = mapped_column(String(200))  # Organismo específico

    # URL del registro en BDNS (Beneficiary Record)
    url_bdns: Mapped[Optional[str]] = mapped_column(String(500))

    entidad_religiosa: Mapped["EntidadReligiosa"] = relationship(
        "EntidadReligiosa",
        back_populates="subvenciones",
    )


class EntidadReligiosaTitular(TitularBase, Base):
    __tablename__ = "entidades_religiosas_titulares"

    entidad_religiosa_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.entidades_religiosas.id", ondelete="CASCADE"),
        index=True,
    )

    entidad_religiosa: Mapped["EntidadReligiosa"] = relationship(
        "EntidadReligiosa",
        back_populates="titulares",
    )


class Sede(UUIDPKMixin, AuditMixin, Base):
    """
    Punto de unión entre una entidad religiosa y el edificio físico que ocupa.

    Una entidad puede tener:
      - Varias sedes simultáneas (casa madre + casas provinciales)
      - Sedes históricas (vigente_hasta no nulo)
      - Sedes sin inmueble registrado aún (inmueble_id nullable)

    El FK a Inmueble es nullable para permitir registrar la sede (con dirección
    textual) antes de que el inmueble esté dado de alta en el sistema.
    """
    __tablename__ = "sedes"

    # ── Quién ocupa ───────────────────────────────────────────────────────────
    entidad_religiosa_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.entidades_religiosas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Qué edificio ──────────────────────────────────────────────────────────
    inmueble_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.inmuebles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Tipo de sede ──────────────────────────────────────────────────────────
    # DOMICILIO_SOCIAL · SEDE_OPERATIVA · SEDE_HISTORICA · OTRA
    tipo_sede: Mapped[str] = mapped_column(
        String(30), nullable=False, default="DOMICILIO_SOCIAL", index=True,
    )

    # ── Temporalidad ──────────────────────────────────────────────────────────
    vigente_desde: Mapped[Optional[Date]] = mapped_column(Date, nullable=True, index=True)
    vigente_hasta: Mapped[Optional[Date]] = mapped_column(Date, nullable=True, index=True)

    # ── Dirección (cuando no hay inmueble vinculado aún) ──────────────────────
    nombre_via:    Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    numero_via:    Mapped[Optional[str]] = mapped_column(String(50),  nullable=True)
    codigo_postal: Mapped[Optional[str]] = mapped_column(String(10),  nullable=True)
    municipio_id:  Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.municipios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    entidad_religiosa: Mapped["EntidadReligiosa"] = relationship(
        "EntidadReligiosa", back_populates="sedes",
    )
    inmueble: Mapped[Optional["Inmueble"]] = relationship(
        "Inmueble",
        primaryjoin="foreign(Sede.inmueble_id) == Inmueble.id",
        back_populates="sedes",
    )
    municipio: Mapped[Optional["Municipio"]] = relationship(
        "Municipio",
        primaryjoin="foreign(Sede.municipio_id) == Municipio.id",
    )
