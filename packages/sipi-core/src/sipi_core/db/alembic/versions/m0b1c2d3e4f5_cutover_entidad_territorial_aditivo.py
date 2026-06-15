"""cutover entidad territorial (Fase 2, aditivo)

Strangler step: añade `entidad_territorial_id` (y `ambito_entidad_territorial_id`
en asociaciones) a todos los consumidores geográficos y los rellena por backfill
desde `entidades_territoriales.origen_tabla/origen_id`, mapeando los FK viejos
(municipio_id > provincia_id > comunidad_autonoma_id, el más profundo disponible).

ADITIVO: NO toca las tablas/columnas viejas (comunidades_autonomas/provincias/
municipios/entidades_locales_menores siguen ahí). Su retirada va en una migración
posterior, cuando se verifique el backfill contra datos reales.

Idempotente y seguro si `entidades_territoriales` está vacía (el backfill no
encuentra nada y deja las columnas a NULL).

Revision ID: m0b1c2d3e4f5
Revises: l9a0b1c2d3e4
Create Date: 2026-06-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "m0b1c2d3e4f5"
down_revision: Union[str, None] = "l9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"

NEW_COLS = ("entidad_territorial_id", "ambito_entidad_territorial_id")

# (columna fuente vieja, origen_tabla en entidades_territoriales), de más profundo a menos.
SRC_PRIORITY = [
    ("municipio_id", "municipios"),
    ("provincia_id", "provincias"),
    ("comunidad_autonoma_id", "comunidades_autonomas"),
]
SRC_PRIORITY_AMBITO = [
    ("ambito_municipio_id", "municipios"),
    ("ambito_provincia_id", "provincias"),
    ("ambito_comunidad_autonoma_id", "comunidades_autonomas"),
]


def _tables_with_new_cols(metadata):
    """Tablas del modelo (en SCHEMA) que definen alguna de las columnas nuevas."""
    for table in metadata.tables.values():
        if (table.schema or SCHEMA) != SCHEMA:
            continue
        targets = [c.name for c in table.columns if c.name in NEW_COLS]
        if targets:
            yield table.name, targets


def upgrade() -> None:
    bind = op.get_bind()
    from sipi_core.models import Base  # registra el metadata completo

    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names(schema=SCHEMA))

    # 1) ADD COLUMN + índice (aditivo, nullable, sin constraint FK — estilo del repo)
    for table_name, targets in _tables_with_new_cols(Base.metadata):
        if table_name not in existing_tables:
            continue
        db_cols = {c["name"] for c in insp.get_columns(table_name, schema=SCHEMA)}
        for col in targets:
            if col not in db_cols:
                op.add_column(table_name, sa.Column(col, sa.String(36), nullable=True), schema=SCHEMA)
                op.execute(f'CREATE INDEX IF NOT EXISTS ix_{table_name}_{col} ON {SCHEMA}.{table_name} ("{col}")')

    # 2) BACKFILL desde origen_tabla/origen_id (solo si la tabla puente existe)
    if "entidades_territoriales" not in existing_tables:
        return
    insp = sa.inspect(bind)
    for table_name, targets in _tables_with_new_cols(Base.metadata):
        if table_name not in existing_tables:
            continue
        cols = {c["name"] for c in insp.get_columns(table_name, schema=SCHEMA)}
        if "entidad_territorial_id" in targets and "entidad_territorial_id" in cols:
            for src, origen in SRC_PRIORITY:
                if src in cols:
                    _backfill(table_name, "entidad_territorial_id", src, origen)
        if "ambito_entidad_territorial_id" in targets and "ambito_entidad_territorial_id" in cols:
            for src, origen in SRC_PRIORITY_AMBITO:
                if src in cols:
                    _backfill(table_name, "ambito_entidad_territorial_id", src, origen)


def _backfill(table: str, target: str, src: str, origen: str) -> None:
    # El `AND t.{target} IS NULL` hace que gane el nivel más profundo (se aplica primero).
    op.execute(f"""
        UPDATE {SCHEMA}.{table} t
        SET {target} = et.id
        FROM {SCHEMA}.entidades_territoriales et
        WHERE et.origen_tabla = '{origen}'
          AND et.origen_id = t.{src}
          AND t.{src} IS NOT NULL
          AND t.{target} IS NULL
    """)


def downgrade() -> None:
    bind = op.get_bind()
    from sipi_core.models import Base
    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names(schema=SCHEMA))
    for table_name, targets in _tables_with_new_cols(Base.metadata):
        if table_name not in existing_tables:
            continue
        for col in targets:
            op.execute(f'DROP INDEX IF EXISTS {SCHEMA}.ix_{table_name}_{col}')
            op.execute(f'ALTER TABLE {SCHEMA}.{table_name} DROP COLUMN IF EXISTS {col}')
