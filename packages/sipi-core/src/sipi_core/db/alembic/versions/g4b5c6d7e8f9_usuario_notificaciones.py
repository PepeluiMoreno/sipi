"""Usuario.acepta_notificaciones (consentimiento de notificaciones).

Aditiva. Esquema B (sipi).

Revision ID: g4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'g4b5c6d7e8f9'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    cols = {c["name"] for c in insp.get_columns("usuarios", schema=SCHEMA)}
    if "acepta_notificaciones" not in cols:
        op.add_column("usuarios",
                      sa.Column("acepta_notificaciones", sa.Boolean(), nullable=False, server_default=sa.false()),
                      schema=SCHEMA)


def downgrade() -> None:
    op.execute("ALTER TABLE sipi.usuarios DROP COLUMN IF EXISTS acepta_notificaciones")
