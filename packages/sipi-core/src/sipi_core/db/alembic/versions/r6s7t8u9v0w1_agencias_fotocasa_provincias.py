"""Añade fotocasa_id/fuente a agencias_inmobiliarias y crea tabla agencias_provincias

Revision ID: r6s7t8u9v0w1
Revises: q5r6s7t8u9v0
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa

revision      = 'r6s7t8u9v0w1'
down_revision = 'q5r6s7t8u9v0'
branch_labels = None
depends_on    = None

SCHEMA = "sipi"


def upgrade() -> None:
    # ── 1. Nuevas columnas en agencias_inmobiliarias ──────────────────────────
    op.add_column(
        "agencias_inmobiliarias",
        sa.Column("fotocasa_id", sa.String(50), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "agencias_inmobiliarias",
        sa.Column("fuente", sa.String(50), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_agencias_inmobiliarias_fotocasa_id",
        "agencias_inmobiliarias", ["fotocasa_id"],
        unique=True, schema=SCHEMA,
    )
    op.create_index(
        "ix_agencias_inmobiliarias_fuente",
        "agencias_inmobiliarias", ["fuente"],
        schema=SCHEMA,
    )

    # ── 2. Tabla pivot agencias_provincias ────────────────────────────────────
    op.create_table(
        "agencias_provincias",
        sa.Column("id",              sa.String(36), primary_key=True),
        sa.Column("agencia_id",      sa.String(36), sa.ForeignKey(f"{SCHEMA}.agencias_inmobiliarias.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provincia_id",    sa.String(36), sa.ForeignKey(f"{SCHEMA}.provincias.id"),              nullable=False),
        sa.Column("fuente",          sa.String(50),  nullable=False),
        sa.Column("inmuebles_zona",  sa.Integer(),   nullable=True),
        sa.Column("inmuebles_total", sa.Integer(),   nullable=True),
        sa.Column("precio_minimo",   sa.String(30),  nullable=True),
        sa.Column("url_busqueda",    sa.String(500), nullable=True),
        sa.Column("created_at",      sa.DateTime(),  nullable=False),
        sa.Column("updated_at",      sa.DateTime(),  nullable=True),
        sa.UniqueConstraint("agencia_id", "provincia_id", "fuente", name="uq_agencia_provincia_fuente"),
        schema=SCHEMA,
    )
    op.create_index("ix_agencias_provincias_agencia_id",   "agencias_provincias", ["agencia_id"],   schema=SCHEMA)
    op.create_index("ix_agencias_provincias_provincia_id", "agencias_provincias", ["provincia_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("agencias_provincias", schema=SCHEMA)
    op.drop_index("ix_agencias_inmobiliarias_fuente",      table_name="agencias_inmobiliarias", schema=SCHEMA)
    op.drop_index("ix_agencias_inmobiliarias_fotocasa_id", table_name="agencias_inmobiliarias", schema=SCHEMA)
    op.drop_column("agencias_inmobiliarias", "fuente",      schema=SCHEMA)
    op.drop_column("agencias_inmobiliarias", "fotocasa_id", schema=SCHEMA)
