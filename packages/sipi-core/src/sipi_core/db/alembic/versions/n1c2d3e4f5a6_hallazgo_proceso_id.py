"""hallazgo.proceso_id — enlaza cada hallazgo con el ProcesoVigilancia que lo generó

Aditivo. Esquema B (sipi).

Revision ID: n1c2d3e4f5a6
Revises: m0b1c2d3e4f5
Create Date: 2026-06-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "n1c2d3e4f5a6"
down_revision: Union[str, None] = "m0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tablas = set(insp.get_table_names(schema=SCHEMA))
    if "hallazgos" not in tablas:
        return
    cols = {c["name"] for c in insp.get_columns("hallazgos", schema=SCHEMA)}
    if "proceso_id" not in cols:
        op.add_column("hallazgos", sa.Column("proceso_id", sa.String(36), nullable=True), schema=SCHEMA)
        op.execute(f'CREATE INDEX IF NOT EXISTS ix_hallazgos_proceso_id ON {SCHEMA}.hallazgos (proceso_id)')
        insp = sa.inspect(bind)
        fks = {fk.get("name") for fk in insp.get_foreign_keys("hallazgos", schema=SCHEMA)}
        if "fk_hallazgos_proceso_id" not in fks and "procesos_vigilancia" in tablas:
            op.create_foreign_key("fk_hallazgos_proceso_id", "hallazgos", "procesos_vigilancia",
                                  ["proceso_id"], ["id"], source_schema=SCHEMA, referent_schema=SCHEMA,
                                  ondelete="SET NULL")


def downgrade() -> None:
    op.execute(f"ALTER TABLE {SCHEMA}.hallazgos DROP CONSTRAINT IF EXISTS fk_hallazgos_proceso_id")
    op.execute(f"DROP INDEX IF EXISTS {SCHEMA}.ix_hallazgos_proceso_id")
    op.execute(f"ALTER TABLE {SCHEMA}.hallazgos DROP COLUMN IF EXISTS proceso_id")
