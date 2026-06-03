"""comunicacion + certeza expediente (aditivo)

Crea las tablas del módulo `comunicacion` (tipos_notificacion, notificaciones) y
añade a `expedientes` las columnas `certeza` (enum) y `confianza` (numeric).
Esquema B (sipi). Patrón dinámico probado (create_all checkfirst + add_column de
las columnas del modelo ausentes). Aditivo; no toca datos.

Revision ID: 4835b03a7d0b
Revises: ebf00235d93c
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '4835b03a7d0b'
down_revision: Union[str, None] = 'ebf00235d93c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    from sipi_core.models import Base
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names(schema=SCHEMA))

    to_create = [t for t in Base.metadata.sorted_tables
                 if (t.schema or SCHEMA) == SCHEMA and t.name not in existing]
    if to_create:
        Base.metadata.create_all(bind=bind, tables=to_create, checkfirst=True)

    insp = sa.inspect(bind)
    for table in Base.metadata.tables.values():
        if (table.schema or SCHEMA) != SCHEMA or table.name not in existing:
            continue
        db_cols = {c["name"] for c in insp.get_columns(table.name, schema=SCHEMA)}
        for col in table.columns:
            if col.name in db_cols:
                continue
            coltype = col.type
            if isinstance(coltype, sa.Enum):
                postgresql.ENUM(*coltype.enums, name=coltype.name).create(bind, checkfirst=True)
                newtype = postgresql.ENUM(name=coltype.name, create_type=False)
            else:
                newtype = coltype.copy() if hasattr(coltype, "copy") else coltype
            op.add_column(table.name, sa.Column(col.name, newtype, nullable=True), schema=SCHEMA)


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.notificaciones CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.tipos_notificacion CASCADE")
    op.execute(f"ALTER TABLE {SCHEMA}.expedientes DROP COLUMN IF EXISTS confianza")
    op.execute(f"ALTER TABLE {SCHEMA}.expedientes DROP COLUMN IF EXISTS certeza")
    op.execute("DROP TYPE IF EXISTS prioridad_notif")
    op.execute("DROP TYPE IF EXISTS certeza_hallazgo")
