"""Inmueble.entidad_territorial_id (referencia al modelo territorial recursivo) + backfill.

Fase 2 (cutover, paso 1): el inmueble apunta a una EntidadTerritorial (nodo más profundo).
Backfill desde municipio_id usando el mapeo origen del ETL. Coexiste con municipio_id
hasta deprecar las tablas tipadas.

Revision ID: j7e8f9a0b1c2
Revises: i6d7e8f9a0b1
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'j7e8f9a0b1c2'
down_revision: Union[str, None] = 'i6d7e8f9a0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    cols = {c["name"] for c in insp.get_columns("inmuebles", schema=SCHEMA)}
    if "entidad_territorial_id" not in cols:
        op.add_column("inmuebles", sa.Column("entidad_territorial_id", sa.String(36)), schema=SCHEMA)
        op.create_index("ix_sipi_inmuebles_entidad_territorial_id", "inmuebles",
                        ["entidad_territorial_id"], schema=SCHEMA)
        op.create_foreign_key("fk_inmuebles_entidad_territorial_id", "inmuebles",
                              "entidades_territoriales", ["entidad_territorial_id"], ["id"],
                              source_schema=SCHEMA, referent_schema=SCHEMA, ondelete="SET NULL")
    # Backfill: municipio_id → EntidadTerritorial (origen='municipios')
    op.execute("""
        UPDATE sipi.inmuebles i
        SET entidad_territorial_id = et.id
        FROM sipi.entidades_territoriales et
        WHERE et.origen_tabla = 'municipios' AND et.origen_id = i.municipio_id
          AND i.municipio_id IS NOT NULL AND i.entidad_territorial_id IS NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE sipi.inmuebles DROP CONSTRAINT IF EXISTS fk_inmuebles_entidad_territorial_id")
    op.execute("DROP INDEX IF EXISTS sipi.ix_sipi_inmuebles_entidad_territorial_id")
    op.execute("ALTER TABLE sipi.inmuebles DROP COLUMN IF EXISTS entidad_territorial_id")
