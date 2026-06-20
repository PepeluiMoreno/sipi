"""Toponimo.entidad_territorial_id (cutover al modelo territorial recursivo) + backfill.

Fase 2: el gazetteer (Toponimo) referencia EntidadTerritorial. Backfill mapeando
(nivel, entidad_id) → (origen_tabla, origen_id) del ETL. `nivel`/`entidad_id` se deprecan luego.

Revision ID: k8f9a0b1c2d3
Revises: j7e8f9a0b1c2
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'k8f9a0b1c2d3'
down_revision: Union[str, None] = 'j7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    cols = {c["name"] for c in insp.get_columns("toponimos", schema=SCHEMA)}
    if "entidad_territorial_id" not in cols:
        op.add_column("toponimos", sa.Column("entidad_territorial_id", sa.String(36)), schema=SCHEMA)
        op.create_index("ix_sipi_toponimos_entidad_territorial_id", "toponimos",
                        ["entidad_territorial_id"], schema=SCHEMA)
        op.create_foreign_key("fk_toponimos_entidad_territorial_id", "toponimos",
                              "entidades_territoriales", ["entidad_territorial_id"], ["id"],
                              source_schema=SCHEMA, referent_schema=SCHEMA, ondelete="SET NULL")
    # Backfill: (nivel, entidad_id) → EntidadTerritorial (origen_tabla, origen_id)
    op.execute("""
        UPDATE sipi.toponimos t
        SET entidad_territorial_id = et.id
        FROM sipi.entidades_territoriales et
        WHERE et.origen_id = t.entidad_id
          AND et.origen_tabla = (CASE t.nivel
                WHEN 'comunidad_autonoma'  THEN 'comunidades_autonomas'
                WHEN 'provincia'           THEN 'provincias'
                WHEN 'municipio'           THEN 'municipios'
                WHEN 'entidad_local_menor' THEN 'entidades_locales_menores'
              END)
          AND t.entidad_territorial_id IS NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE sipi.toponimos DROP CONSTRAINT IF EXISTS fk_toponimos_entidad_territorial_id")
    op.execute("DROP INDEX IF EXISTS sipi.ix_sipi_toponimos_entidad_territorial_id")
    op.execute("ALTER TABLE sipi.toponimos DROP COLUMN IF EXISTS entidad_territorial_id")
