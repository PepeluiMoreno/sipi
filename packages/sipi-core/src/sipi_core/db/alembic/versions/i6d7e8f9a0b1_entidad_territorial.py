"""EntidadTerritorial: tabla recursiva única para la jerarquía territorial (admin + eclesiástico).

Aditiva (Fase 1 strangler): crea la tabla; las 7 tablas originales se conservan.
La población se hace por ETL (services/seed_entidades_territoriales.py).

Revision ID: i6d7e8f9a0b1
Revises: g4b5c6d7e8f9
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op

from sipi_core.db.registry import Base
import sipi_core.models  # noqa: F401  (registra EntidadTerritorial en metadata)

revision: str = 'i6d7e8f9a0b1'
down_revision: Union[str, None] = 'g4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    Base.metadata.tables[f"{SCHEMA}.entidades_territoriales"].create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sipi.entidades_territoriales")
