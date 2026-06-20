"""subvenciones_entidades

Crea la tabla sipi.subvenciones_entidades para almacenar las concesiones
BDNS (Base de Datos Nacional de Subvenciones) vinculadas a entidades religiosas.

Cada fila es una concesión individual de la BDNS. El campo cod_concesion
(ej: 'SB146548130') actúa como código natural único para idempotencia.

Revision ID: j8k9l0m1n2o3
Revises: i7j8k9l0m1n2
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision    = 'j8k9l0m1n2o3'
down_revision = 'i7j8k9l0m1n2'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade() -> None:
    op.create_table(
        'subvenciones_entidades',
        sa.Column('id',                    sa.String(36),  nullable=False, primary_key=True),
        sa.Column('entidad_religiosa_id',  sa.String(36),  nullable=False),
        # ── Código natural BDNS ────────────────────────────────────────────────
        sa.Column('cod_concesion',         sa.String(30),  nullable=False),
        sa.Column('id_bdns',               sa.Integer(),   nullable=True),
        sa.Column('id_persona_bdns',       sa.Integer(),   nullable=True),
        # ── Datos económicos ───────────────────────────────────────────────────
        sa.Column('fecha_concesion',       sa.DateTime(),  nullable=True),
        sa.Column('fecha_alta_bdns',       sa.DateTime(),  nullable=True),
        sa.Column('importe',               sa.Float(),     nullable=True),
        sa.Column('ayuda_equivalente',     sa.Float(),     nullable=True),
        # ── Tipo y descripción ─────────────────────────────────────────────────
        sa.Column('instrumento',           sa.String(200), nullable=True),
        sa.Column('beneficiario_bdns',     sa.String(500), nullable=True),
        # ── Convocatoria ───────────────────────────────────────────────────────
        sa.Column('id_convocatoria_bdns',  sa.Integer(),   nullable=True),
        sa.Column('numero_convocatoria',   sa.String(50),  nullable=True),
        sa.Column('convocatoria',          sa.String(500), nullable=True),
        sa.Column('descripcion_cooficial', sa.String(500), nullable=True),
        sa.Column('tiene_proyecto',        sa.Boolean(),   nullable=True),
        sa.Column('codigo_invente',        sa.String(50),  nullable=True),
        # ── Organismo concedente ───────────────────────────────────────────────
        sa.Column('nivel1',                sa.String(50),  nullable=True),
        sa.Column('nivel2',                sa.String(200), nullable=True),
        sa.Column('nivel3',                sa.String(200), nullable=True),
        sa.Column('url_bdns',              sa.String(500), nullable=True),
        # ── Auditoría ─────────────────────────────────────────────────────────
        sa.Column('created_at',            sa.DateTime(),  nullable=True),
        sa.Column('updated_at',            sa.DateTime(),  nullable=True),
        sa.Column('deleted_at',            sa.DateTime(),  nullable=True),
        sa.ForeignKeyConstraint(
            ['entidad_religiosa_id'], [f'{S}.entidades_religiosas.id'],
            name='fk_subvenciones_entidad_religiosa', ondelete='CASCADE',
        ),
        sa.UniqueConstraint('cod_concesion', name='uq_subvenciones_cod_concesion'),
        schema=S,
    )
    op.create_index('ix_subv_entidad',            'subvenciones_entidades', ['entidad_religiosa_id'], schema=S)
    op.create_index('ix_subv_cod_concesion',      'subvenciones_entidades', ['cod_concesion'],        schema=S)
    op.create_index('ix_subv_id_bdns',            'subvenciones_entidades', ['id_bdns'],              schema=S)
    op.create_index('ix_subv_id_persona',         'subvenciones_entidades', ['id_persona_bdns'],      schema=S)
    op.create_index('ix_subv_id_convocatoria',    'subvenciones_entidades', ['id_convocatoria_bdns'], schema=S)
    op.create_index('ix_subv_numero_convocatoria','subvenciones_entidades', ['numero_convocatoria'],   schema=S)
    op.create_index('ix_subv_fecha_concesion',    'subvenciones_entidades', ['fecha_concesion'],       schema=S)


def downgrade() -> None:
    for idx in (
        'ix_subv_entidad', 'ix_subv_cod_concesion', 'ix_subv_id_bdns',
        'ix_subv_id_persona', 'ix_subv_id_convocatoria',
        'ix_subv_numero_convocatoria', 'ix_subv_fecha_concesion',
    ):
        try:
            op.drop_index(idx, table_name='subvenciones_entidades', schema=S)
        except Exception:
            pass
    op.drop_table('subvenciones_entidades', schema=S)
