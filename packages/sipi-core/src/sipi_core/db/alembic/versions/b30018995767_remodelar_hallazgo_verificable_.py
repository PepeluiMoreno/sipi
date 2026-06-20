"""remodelar: Hallazgo (verificable) + Expediente dosier

El flujo de validación pasa del Expediente al Hallazgo: los watchers extraen datos
(`hallazgos`, estado PENDIENTE + scoring); el humano los comprueba (verificar/
descartar) y, al verificar, se abre/engrosa un `Expediente` (dosier del inmueble).

`expedientes` cambia de forma (workflow → dosier) y está VACÍO, así que se recrea.
Se crea la tabla `hallazgos`. Esquema B (sipi). Datos de dominio intactos.

Revision ID: b30018995767
Revises: 4835b03a7d0b
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b30018995767'
down_revision: Union[str, None] = '4835b03a7d0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    # expedientes (vacío) cambia de forma: workflow → dosier. Recrear.
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.expedientes CASCADE")
    op.execute("DROP TYPE IF EXISTS estado_expediente")  # ya no se usa

    # Recrear expedientes (nueva forma) + crear hallazgos (enums checkfirst)
    from sipi_core.models import Base
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names(schema=SCHEMA))
    to_create = [t for t in Base.metadata.sorted_tables
                 if (t.schema or SCHEMA) == SCHEMA and t.name not in existing]
    if to_create:
        Base.metadata.create_all(bind=bind, tables=to_create, checkfirst=True)


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.hallazgos CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.expedientes CASCADE")
    op.execute("DROP TYPE IF EXISTS estado_hallazgo")
