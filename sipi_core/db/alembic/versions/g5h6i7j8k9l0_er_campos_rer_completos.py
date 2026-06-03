"""er_campos_rer_completos

Añade todos los campos del RER que faltaban tras la migración inicial:
  - numero_registro_antiguo  (ya puede existir en BD — idempotente)
  - seccion_rer              (ídem)
  - congregacion             (ídem)
  - ambito_geografico        (ídem)
  - nivel_superior_id + FK   (ídem)
  - nif                      (NUEVO)
  - fecha_aprobacion_estatutos (NUEVO)
  - federaciones             (NUEVO — texto libre del RER)
  - entidades_federadas      (NUEVO — texto libre del RER)
  - lugares_culto            (NUEVO — texto libre del RER)

Revision ID: g5h6i7j8k9l0
Revises: f4g5h6i7j8k9
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision    = 'g5h6i7j8k9l0'
down_revision = 'f4g5h6i7j8k9'
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

    # ── Columnas que pueden existir ya (creadas por SQL directo en etapas anteriores) ──
    idempotentes = [
        ('numero_registro_antiguo', sa.String(50)),
        ('seccion_rer',             sa.String(50)),
        ('congregacion',            sa.String(500)),
        ('ambito_geografico',       sa.String(20)),
        ('nivel_superior_id',       sa.String(36)),
    ]
    for col, typ in idempotentes:
        if not _col_exists(t, col):
            op.add_column(t, sa.Column(col, typ, nullable=True), schema=S)

    # FK self-referential nivel_superior_id
    if not _idx_exists('ix_er_nivel_superior'):
        op.create_index('ix_er_nivel_superior', t, ['nivel_superior_id'], schema=S)

    # ── Columnas nuevas ────────────────────────────────────────────────────────
    nuevas = [
        ('nif',                       sa.String(20)),
        ('fecha_aprobacion_estatutos', sa.DateTime()),
        ('federaciones',              sa.Text()),
        ('entidades_federadas',       sa.Text()),
        ('lugares_culto',             sa.Text()),
    ]
    for col, typ in nuevas:
        if not _col_exists(t, col):
            op.add_column(t, sa.Column(col, typ, nullable=True), schema=S)

    if not _idx_exists('ix_er_nif'):
        op.create_index('ix_er_nif', t, ['nif'], schema=S)


def downgrade() -> None:
    t = 'entidades_religiosas'
    for idx in ('ix_er_nif', 'ix_er_nivel_superior'):
        try:
            op.drop_index(idx, table_name=t, schema=S)
        except Exception:
            pass
    for col in ('nif', 'fecha_aprobacion_estatutos', 'federaciones',
                'entidades_federadas', 'lugares_culto'):
        try:
            op.drop_column(t, col, schema=S)
        except Exception:
            pass
