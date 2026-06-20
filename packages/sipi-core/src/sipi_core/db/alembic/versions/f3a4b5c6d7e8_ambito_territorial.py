"""Ámbito territorial: Asociacion.ambito_* + UsuarioRol territorio (CCAA/provincia/municipio).

Aditiva. Esquema B (sipi). La asociación define su área de operación; cada
asignación rol↔usuario (usuario_rol) se acota a un territorio dentro de ese ámbito.
La FK más profunda no nula define el nivel; todas nulas = nacional.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"

# (tabla, prefijo de columnas)
_DESTINOS = [("asociaciones", "ambito_"), ("usuario_rol", "")]
# (sufijo de columna, tabla de geografía)
_GEO = [("comunidad_autonoma_id", "comunidades_autonomas"),
        ("provincia_id", "provincias"),
        ("municipio_id", "municipios")]


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for tabla, prefijo in _DESTINOS:
        cols = {c["name"] for c in insp.get_columns(tabla, schema=SCHEMA)}
        for sufijo, geo_tabla in _GEO:
            col = f"{prefijo}{sufijo}"
            if col in cols:
                continue
            op.add_column(tabla, sa.Column(col, sa.String(36)), schema=SCHEMA)
            op.create_index(f"ix_{SCHEMA}_{tabla}_{col}", tabla, [col], schema=SCHEMA)
            op.create_foreign_key(f"fk_{tabla}_{col}", tabla, geo_tabla, [col], ["id"],
                                  source_schema=SCHEMA, referent_schema=SCHEMA, ondelete="SET NULL")


def downgrade() -> None:
    for tabla, prefijo in _DESTINOS:
        for sufijo, _ in _GEO:
            col = f"{prefijo}{sufijo}"
            op.execute(f"ALTER TABLE {SCHEMA}.{tabla} DROP CONSTRAINT IF EXISTS fk_{tabla}_{col}")
            op.execute(f"DROP INDEX IF EXISTS {SCHEMA}.ix_{SCHEMA}_{tabla}_{col}")
            op.execute(f"ALTER TABLE {SCHEMA}.{tabla} DROP COLUMN IF EXISTS {col}")
