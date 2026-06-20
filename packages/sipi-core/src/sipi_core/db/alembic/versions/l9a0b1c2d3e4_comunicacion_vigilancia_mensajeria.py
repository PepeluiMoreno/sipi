"""comunicacion: procesos de vigilancia + mensajeria + avisos enriquecidos

Porte adaptado de la rama `feat/etl-odm-comunicacion` al dominio local de
comunicación (sin duplicar la tabla de avisos):

- Tablas nuevas: procesos_vigilancia (+ destinatarios por rol/usuario) y
  mensajería usuario<->usuario (canales, canal_miembro, mensajes).
- `notificaciones` se enriquece con `proceso_id`, `payload` (JSONB) y
  `clave_dedupe` (idempotencia) — plegando aquí el valor de `Aviso` del patch en
  vez de crear una tabla paralela.

Aditivo. Esquema B (sipi). Patrón model-driven (create_all checkfirst + add_column).

Revision ID: l9a0b1c2d3e4
Revises: k8f9a0b1c2d3
Create Date: 2026-06-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "l9a0b1c2d3e4"
down_revision: Union[str, None] = "k8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"

NEW_TABLES = [
    "procesos_vigilancia",
    "proceso_destinatario_rol",
    "proceso_destinatario_usuario",
    "canales",
    "canal_miembro",
    "mensajes",
]

# Columnas nuevas en notificaciones (aditivo, nullable)
NOTIF_NEW_COLS = [
    ("proceso_id", sa.String(36)),
    ("payload", postgresql.JSONB()),
    ("clave_dedupe", sa.String(255)),
]


def upgrade() -> None:
    bind = op.get_bind()
    from sipi_core.models import Base  # registra todos los modelos (incl. los nuevos)

    insp = sa.inspect(bind)
    existing = set(insp.get_table_names(schema=SCHEMA))

    # 1) Crear las tablas nuevas desde el metadata de los modelos
    to_create = [t for t in Base.metadata.sorted_tables
                 if t.name in NEW_TABLES and t.name not in existing]
    if to_create:
        Base.metadata.create_all(bind=bind, tables=to_create, checkfirst=True)

    # 2) Enriquecer notificaciones (si la tabla existe)
    insp = sa.inspect(bind)
    if "notificaciones" in set(insp.get_table_names(schema=SCHEMA)):
        notif_cols = {c["name"] for c in insp.get_columns("notificaciones", schema=SCHEMA)}
        for name, type_ in NOTIF_NEW_COLS:
            if name not in notif_cols:
                op.add_column("notificaciones", sa.Column(name, type_, nullable=True), schema=SCHEMA)

        insp = sa.inspect(bind)
        idx = {i["name"] for i in insp.get_indexes("notificaciones", schema=SCHEMA)}
        if "uq_notificaciones_clave_dedupe" not in idx:
            op.create_index("uq_notificaciones_clave_dedupe", "notificaciones",
                            ["clave_dedupe"], unique=True, schema=SCHEMA)

        fks = {fk.get("name") for fk in insp.get_foreign_keys("notificaciones", schema=SCHEMA)}
        if "fk_notificaciones_proceso_id" not in fks and "procesos_vigilancia" in existing | set(NEW_TABLES):
            op.create_foreign_key("fk_notificaciones_proceso_id", "notificaciones",
                                  "procesos_vigilancia", ["proceso_id"], ["id"],
                                  source_schema=SCHEMA, referent_schema=SCHEMA, ondelete="SET NULL")


def downgrade() -> None:
    op.execute(f"ALTER TABLE {SCHEMA}.notificaciones DROP CONSTRAINT IF EXISTS fk_notificaciones_proceso_id")
    op.execute(f"DROP INDEX IF EXISTS {SCHEMA}.uq_notificaciones_clave_dedupe")
    for col in ("clave_dedupe", "payload", "proceso_id"):
        op.execute(f"ALTER TABLE {SCHEMA}.notificaciones DROP COLUMN IF EXISTS {col}")
    for t in ("mensajes", "canal_miembro", "canales",
              "proceso_destinatario_usuario", "proceso_destinatario_rol", "procesos_vigilancia"):
        op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{t} CASCADE")
