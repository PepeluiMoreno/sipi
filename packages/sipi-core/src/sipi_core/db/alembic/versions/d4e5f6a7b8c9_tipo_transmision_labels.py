"""Añadir denominacion_transmitente y denominacion_adquiriente a tipos_transmision

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-18

Permite configurar en la tipología los literales que se muestran para
transmitente y adquiriente según el tipo de transmisión:
  - Compraventa  → Vendedor / Comprador
  - Cesión       → Cedente / Cesionario
  - Donación     → Donante / Donatario
  - Herencia     → Causante / Heredero
  - etc.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'app'


def upgrade() -> None:
    op.add_column('tipos_transmision',
        sa.Column('denominacion_transmitente', sa.String(100), nullable=True),
        schema=SCHEMA,
    )
    op.add_column('tipos_transmision',
        sa.Column('denominacion_adquiriente', sa.String(100), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column('tipos_transmision', 'denominacion_adquiriente', schema=SCHEMA)
    op.drop_column('tipos_transmision', 'denominacion_transmitente', schema=SCHEMA)
