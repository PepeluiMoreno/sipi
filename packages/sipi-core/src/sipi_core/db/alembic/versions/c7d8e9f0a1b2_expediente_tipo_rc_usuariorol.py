"""Expediente.tipo/datos + Inmueble.referencia_catastral/fuente_coordenadas
+ InmuebleDocumento.expediente_id + promover usuario_rol a modelo (id/PK).

Aditiva salvo el restructure de usuario_rol (add id, cambia PK compuesta → id +
UNIQUE(usuario_id,rol_id)). Esquema B (sipi). Pocos datos (usuario_rol ~1 fila).

Revision ID: c7d8e9f0a1b2
Revises: b30018995767
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b30018995767'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- enums nuevos ---
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='tipo_expediente') "
               "THEN CREATE TYPE tipo_expediente AS ENUM "
               "('catastral','enajenacion','inmatriculacion','proteccion','intervencion','historico','otro'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='fuente_coordenadas') "
               "THEN CREATE TYPE fuente_coordenadas AS ENUM "
               "('manual','osm','wikidata','catastro','geocoder'); END IF; END $$;")

    # --- expedientes: tipo, datos; estado_actual pasa a nullable ---
    ecols = {c["name"] for c in insp.get_columns("expedientes", schema=SCHEMA)}
    if "tipo" not in ecols:
        op.execute("ALTER TABLE sipi.expedientes ADD COLUMN tipo tipo_expediente NOT NULL DEFAULT 'otro'")
        op.create_index("ix_sipi_expedientes_tipo", "expedientes", ["tipo"], schema=SCHEMA)
    if "datos" not in ecols:
        op.add_column("expedientes", sa.Column("datos", postgresql.JSONB), schema=SCHEMA)
    op.execute("ALTER TABLE sipi.expedientes ALTER COLUMN estado_actual DROP NOT NULL")

    # --- inmuebles: referencia_catastral, fuente_coordenadas ---
    icols = {c["name"] for c in insp.get_columns("inmuebles", schema=SCHEMA)}
    if "referencia_catastral" not in icols:
        op.add_column("inmuebles", sa.Column("referencia_catastral", sa.String(20)), schema=SCHEMA)
        op.create_index("ix_sipi_inmuebles_referencia_catastral", "inmuebles", ["referencia_catastral"], schema=SCHEMA)
    if "fuente_coordenadas" not in icols:
        op.execute("ALTER TABLE sipi.inmuebles ADD COLUMN fuente_coordenadas fuente_coordenadas")
        op.create_index("ix_sipi_inmuebles_fuente_coordenadas", "inmuebles", ["fuente_coordenadas"], schema=SCHEMA)

    # --- inmuebles_documentos: expediente_id (sin FK física; deferida) ---
    dcols = {c["name"] for c in insp.get_columns("inmuebles_documentos", schema=SCHEMA)}
    if "expediente_id" not in dcols:
        op.add_column("inmuebles_documentos", sa.Column("expediente_id", sa.String(36)), schema=SCHEMA)
        op.create_index("ix_sipi_inmuebles_documentos_expediente_id", "inmuebles_documentos", ["expediente_id"], schema=SCHEMA)

    # --- usuario_rol → modelo: add id, swap PK, unique(usuario_id,rol_id) ---
    urcols = {c["name"] for c in insp.get_columns("usuario_rol", schema=SCHEMA)}
    if "id" not in urcols:
        op.execute("ALTER TABLE sipi.usuario_rol ADD COLUMN id VARCHAR(36)")
        op.execute("UPDATE sipi.usuario_rol SET id = gen_random_uuid()::text WHERE id IS NULL")
        op.execute("ALTER TABLE sipi.usuario_rol ALTER COLUMN id SET NOT NULL")
        op.execute("ALTER TABLE sipi.usuario_rol DROP CONSTRAINT IF EXISTS usuario_rol_pkey")
        op.execute("ALTER TABLE sipi.usuario_rol ADD CONSTRAINT usuario_rol_pkey PRIMARY KEY (id)")
        op.execute("ALTER TABLE sipi.usuario_rol ADD CONSTRAINT uq_usuario_rol UNIQUE (usuario_id, rol_id)")


def downgrade() -> None:
    op.execute("ALTER TABLE sipi.usuario_rol DROP CONSTRAINT IF EXISTS uq_usuario_rol")
    op.execute("ALTER TABLE sipi.usuario_rol DROP COLUMN IF EXISTS id")
    op.execute("ALTER TABLE sipi.inmuebles_documentos DROP COLUMN IF EXISTS expediente_id")
    op.execute("ALTER TABLE sipi.inmuebles DROP COLUMN IF EXISTS fuente_coordenadas")
    op.execute("ALTER TABLE sipi.inmuebles DROP COLUMN IF EXISTS referencia_catastral")
    op.execute("ALTER TABLE sipi.expedientes DROP COLUMN IF EXISTS datos")
    op.execute("ALTER TABLE sipi.expedientes DROP COLUMN IF EXISTS tipo")
    op.execute("DROP TYPE IF EXISTS tipo_expediente")
    op.execute("DROP TYPE IF EXISTS fuente_coordenadas")
