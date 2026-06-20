"""fase1: tablas de features que faltan (incl. expedientes) + ciclo de vida en inmuebles

Migración ADITIVA y curada (Fase 1, esquema B = sipi). Crea las tablas del modelo
sipi-core que la BD viva no tenía (se calculan dinámicamente: modelo − BD) y añade
las columnas de ciclo de vida a `inmuebles`. NO toca FKs/índices/tipos de tablas
preexistentes: ese drift de integridad (preexistente, de cuando la BD se creó con
create_all) se reconcilia en una migración de integridad dedicada y validada aparte.

Los tipos ENUM ya existentes se respetan vía `create_all(checkfirst=True)`
(SQLAlchemy no recrea tipos que ya existen); los enums nuevos (expediente y ciclo
de vida) se crean aquí.

Revision ID: a25b36811be2
Revises: r6s7t8u9v0w1
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a25b36811be2'
down_revision: Union[str, None] = 'r6s7t8u9v0w1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def _missing_tables(bind):
    """Tablas del modelo (esquema sipi) que aún no existen en la BD, en orden de
    dependencias para que create_all resuelva las FKs entre ellas."""
    from sipi_core.models import Base
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names(schema=SCHEMA))
    out = []
    for t in Base.metadata.sorted_tables:
        if (t.schema or SCHEMA) == SCHEMA and t.name not in existing:
            out.append(t)
    return out


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Crear SOLO las tablas que faltan (calculadas dinámicamente).
    #    create_all(checkfirst=True) no recrea tipos ENUM que ya existen en la BD.
    from sipi_core.models import Base
    tables = _missing_tables(bind)
    if tables:
        Base.metadata.create_all(bind=bind, tables=tables, checkfirst=True)

    # 2) Columnas de ciclo de vida en inmuebles (enums nuevos: se crean aquí).
    estado_ciclo_vida = postgresql.ENUM(
        "inmatriculado", "en_venta", "vendido", "cambio_de_uso", "rehabilitacion",
        name="estado_ciclo_vida",
    )
    geo_quality = postgresql.ENUM(
        "manual", "auto", "missing", name="geo_quality",
    )
    estado_ciclo_vida.create(bind, checkfirst=True)
    geo_quality.create(bind, checkfirst=True)

    insp = sa.inspect(bind)
    inmueble_cols = {c["name"] for c in insp.get_columns("inmuebles", schema=SCHEMA)}

    if "estado_ciclo_vida" not in inmueble_cols:
        op.add_column(
            "inmuebles",
            sa.Column(
                "estado_ciclo_vida",
                postgresql.ENUM(name="estado_ciclo_vida", create_type=False),
                server_default="inmatriculado",
                nullable=False,
            ),
            schema=SCHEMA,
        )
        op.create_index("ix_sipi_inmuebles_estado_ciclo_vida", "inmuebles",
                        ["estado_ciclo_vida"], schema=SCHEMA)

    if "geo_quality" not in inmueble_cols:
        op.add_column(
            "inmuebles",
            sa.Column(
                "geo_quality",
                postgresql.ENUM(name="geo_quality", create_type=False),
                server_default="missing",
                nullable=False,
            ),
            schema=SCHEMA,
        )
        op.create_index("ix_sipi_inmuebles_geo_quality", "inmuebles",
                        ["geo_quality"], schema=SCHEMA)


def downgrade() -> None:
    # Best-effort: revierte columnas/enums de ciclo de vida. Las tablas creadas
    # no se eliminan automáticamente (drop manual si se requiere) para no perder
    # datos que se hubieran cargado tras la migración.
    op.execute("DROP INDEX IF EXISTS sipi.ix_sipi_inmuebles_geo_quality")
    op.execute("DROP INDEX IF EXISTS sipi.ix_sipi_inmuebles_estado_ciclo_vida")
    op.execute("ALTER TABLE sipi.inmuebles DROP COLUMN IF EXISTS geo_quality")
    op.execute("ALTER TABLE sipi.inmuebles DROP COLUMN IF EXISTS estado_ciclo_vida")
    op.execute("DROP TYPE IF EXISTS geo_quality")
    op.execute("DROP TYPE IF EXISTS estado_ciclo_vida")
