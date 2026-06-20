"""Colapsar Miembro en Usuario: el usuario ES el miembro de la asociación.

Revierte la entidad Miembro (tabla `miembros` y `usuarios.miembro_id`) y añade a
`usuarios` la pertenencia directa: `asociacion_id` (FK SET NULL, nullable) y `cargo`.
Usuario regular → asociacion_id puesto; especial/superadmin → NULL + is_sistema.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    ucols = {c["name"] for c in insp.get_columns("usuarios", schema=SCHEMA)}

    # 1) Quitar el enlace usuarios → miembros
    if "miembro_id" in ucols:
        op.execute("ALTER TABLE sipi.usuarios DROP CONSTRAINT IF EXISTS fk_usuarios_miembro_id")
        op.execute("DROP INDEX IF EXISTS sipi.ix_sipi_usuarios_miembro_id")
        op.drop_column("usuarios", "miembro_id", schema=SCHEMA)

    # 2) Eliminar la entidad Miembro
    op.execute("DROP TABLE IF EXISTS sipi.miembros")

    # 3) Pertenencia directa en usuarios
    if "asociacion_id" not in ucols:
        op.add_column("usuarios", sa.Column("asociacion_id", sa.String(36)), schema=SCHEMA)
        op.create_index("ix_sipi_usuarios_asociacion_id", "usuarios", ["asociacion_id"], schema=SCHEMA)
        op.create_foreign_key("fk_usuarios_asociacion_id", "usuarios", "asociaciones",
                              ["asociacion_id"], ["id"], source_schema=SCHEMA,
                              referent_schema=SCHEMA, ondelete="SET NULL")
    if "cargo" not in ucols:
        op.add_column("usuarios", sa.Column("cargo", sa.String(100)), schema=SCHEMA)


def downgrade() -> None:
    # Reversión parcial: la tabla `miembros` no se reconstruye (entidad retirada).
    op.execute("ALTER TABLE sipi.usuarios DROP CONSTRAINT IF EXISTS fk_usuarios_asociacion_id")
    op.execute("DROP INDEX IF EXISTS sipi.ix_sipi_usuarios_asociacion_id")
    op.execute("ALTER TABLE sipi.usuarios DROP COLUMN IF EXISTS asociacion_id")
    op.execute("ALTER TABLE sipi.usuarios DROP COLUMN IF EXISTS cargo")
