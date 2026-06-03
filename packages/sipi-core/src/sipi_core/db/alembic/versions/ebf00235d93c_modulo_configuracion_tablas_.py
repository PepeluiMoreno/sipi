"""modulo configuracion: tablas configuraciones + historial (aditivo)

Crea las tablas `configuraciones` e `historial_configuracion`. Esquema B (sipi).
Patrón dinámico probado: create_all(checkfirst) solo de las tablas del modelo
ausentes. Aditivo; no toca datos.

Revision ID: ebf00235d93c
Revises: e64d9da25474
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'ebf00235d93c'
down_revision: Union[str, None] = 'e64d9da25474'
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


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.historial_configuracion CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.configuraciones CASCADE")
    op.execute("DROP TYPE IF EXISTS tipo_dato_config")
    op.execute("DROP TYPE IF EXISTS ambito_config")
