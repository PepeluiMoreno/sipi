"""er_campos_catastro

Añade campos de enriquecimiento Catastro OVC a entidades_religiosas:
  - referencia_catastral  (código natural catastral, 20 chars, indexado)
  - uso_catastral         (uso declarado en Catastro: Religioso, Educativo…)

Revision ID: i7j8k9l0m1n2
Revises: h6i7j8k9l0m1
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision    = 'i7j8k9l0m1n2'
down_revision = 'h6i7j8k9l0m1'
branch_labels = None
depends_on    = None

S = 'sipi'


def _col_exists(table: str, col: str) -> bool:
    conn = op.get_bind()
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema=:s AND table_name=:t AND column_name=:c"
    ), {"s": S, "t": table, "c": col}).fetchone()
    return r is not None


def _idx_exists(idx: str) -> bool:
    conn = op.get_bind()
    r = conn.execute(sa.text(
        "SELECT 1 FROM pg_indexes WHERE schemaname=:s AND indexname=:i"
    ), {"s": S, "i": idx}).fetchone()
    return r is not None


def upgrade() -> None:
    t = 'entidades_religiosas'
    nuevas = [
        ('referencia_catastral', sa.String(20)),
        ('uso_catastral',        sa.String(50)),
    ]
    for col, typ in nuevas:
        if not _col_exists(t, col):
            op.add_column(t, sa.Column(col, typ, nullable=True), schema=S)

    if not _idx_exists('ix_er_referencia_catastral'):
        op.create_index('ix_er_referencia_catastral', t, ['referencia_catastral'], schema=S)


def downgrade() -> None:
    t = 'entidades_religiosas'
    try:
        op.drop_index('ix_er_referencia_catastral', table_name=t, schema=S)
    except Exception:
        pass
    for col in ('referencia_catastral', 'uso_catastral'):
        try:
            op.drop_column(t, col, schema=S)
        except Exception:
            pass
