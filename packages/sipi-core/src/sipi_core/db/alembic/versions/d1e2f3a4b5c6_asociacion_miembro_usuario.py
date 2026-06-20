"""Asociacion + Miembro + Usuario.miembro_id (mapeo 1:1 usuario→miembro).

Aditiva. Esquema B (sipi). Crea las tablas `asociaciones` y `miembros` a partir de
los modelos (metadata, para no derivar a mano las columnas de los mixins) y añade
`usuarios.miembro_id` (UNIQUE, FK SET NULL). Un Usuario es la proyección de acceso
de un Miembro; los usuarios de sistema quedan con miembro_id NULL.

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sipi_core.db.registry import Base
import sipi_core.models  # noqa: F401  (registra Asociacion/Miembro/Usuario en metadata)

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    md = Base.metadata

    # Crear solo las tablas nuevas (orden: asociaciones antes que miembros por la FK).
    # checkfirst evita recrear el enum `tipoidentificacion`, ya existente.
    for nombre in ("asociaciones", "miembros"):
        md.tables[f"{SCHEMA}.{nombre}"].create(bind, checkfirst=True)

    insp = sa.inspect(bind)
    ucols = {c["name"] for c in insp.get_columns("usuarios", schema=SCHEMA)}
    if "miembro_id" not in ucols:
        op.add_column("usuarios", sa.Column("miembro_id", sa.String(36)), schema=SCHEMA)
        op.create_index("ix_sipi_usuarios_miembro_id", "usuarios", ["miembro_id"],
                        unique=True, schema=SCHEMA)
        op.create_foreign_key("fk_usuarios_miembro_id", "usuarios", "miembros",
                              ["miembro_id"], ["id"], source_schema=SCHEMA,
                              referent_schema=SCHEMA, ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_usuarios_miembro_id", "usuarios", schema=SCHEMA, type_="foreignkey")
    op.drop_index("ix_sipi_usuarios_miembro_id", table_name="usuarios", schema=SCHEMA)
    op.drop_column("usuarios", "miembro_id", schema=SCHEMA)
    op.execute("DROP TABLE IF EXISTS sipi.miembros")
    op.execute("DROP TABLE IF EXISTS sipi.asociaciones")
