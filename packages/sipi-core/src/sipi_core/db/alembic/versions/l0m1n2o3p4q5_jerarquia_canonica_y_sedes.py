"""Jerarquía canónica y tabla sedes

Consolida el modelo canónico eclesiástico:

1. Extiende entidades_religiosas con campos de tipología canónica:
   - tipo_canonico: posición en la jerarquía canónica
     (INSTITUTO_VIDA_CONSAGRADA, ASOCIACION_FIELES, DIOCESIS, PARROQUIA…)
   - subtipo: forma concreta dentro del tipo canónico
     (ORDEN_RELIGIOSA, CONGREGACION, COFRADIA, HERMANDAD, CONVENTO…)
   - parroquia_id: FK a parroquias (solo para asociaciones parroquiales)

2. Crea tabla sedes: enlace entidad_religiosa → inmueble físico.
   - Una entidad puede tener varias sedes a lo largo del tiempo
   - inmueble_id nullable (sede conocida pero inmueble aún no registrado)
   - Temporalidad: vigente_desde / vigente_hasta

Revision ID: l0m1n2o3p4q5
Revises: k9l0m1n2o3p4
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa

revision      = 'l0m1n2o3p4q5'
down_revision = 'k9l0m1n2o3p4'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade() -> None:

    # ── 1. Nuevas columnas en entidades_religiosas ────────────────────────────

    # Tipo canónico: posición en la jerarquía del Derecho Canónico
    # Fuente: CIC 1983, cc. 113-123 (personas jurídicas), 298-329 (asociaciones),
    #         573-746 (institutos vida consagrada)
    op.add_column(
        'entidades_religiosas',
        sa.Column(
            'tipo_canonico',
            sa.String(50),
            nullable=True,
            comment=(
                'Posición canónica: INSTITUTO_VIDA_CONSAGRADA, SOCIEDAD_VIDA_APOSTOLICA, '
                'ASOCIACION_FIELES, PRELATURA_PERSONAL, FUNDACION_PIA, DIOCESIS, PARROQUIA'
            ),
        ),
        schema=S,
    )
    op.create_index('ix_er_tipo_canonico', 'entidades_religiosas', ['tipo_canonico'], schema=S)

    # Subtipo: forma concreta dentro del tipo canónico
    op.add_column(
        'entidades_religiosas',
        sa.Column(
            'subtipo',
            sa.String(50),
            nullable=True,
            comment=(
                'Forma concreta: ORDEN_RELIGIOSA, CONGREGACION, MONASTERIO, CONVENTO, '
                'CASA_RELIGIOSA, COFRADIA, HERMANDAD, ARCHICOFRADIA, ASOCIACION_GENERICA'
            ),
        ),
        schema=S,
    )
    op.create_index('ix_er_subtipo', 'entidades_religiosas', ['subtipo'], schema=S)

    # FK a parroquias (para asociaciones de fieles de ámbito parroquial)
    op.add_column(
        'entidades_religiosas',
        sa.Column(
            'parroquia_id',
            sa.String(36),
            sa.ForeignKey(f'{S}.parroquias.id', ondelete='SET NULL'),
            nullable=True,
            comment='Parroquia a la que está adscrita (solo ASOCIACION_FIELES parroquial)',
        ),
        schema=S,
    )
    op.create_index('ix_er_parroquia_id', 'entidades_religiosas', ['parroquia_id'], schema=S)

    # ── 2. Tabla sedes ────────────────────────────────────────────────────────
    # Punto de unión entre la entidad propietaria/ocupante y el edificio físico.
    # Permite:
    #   - Entidades con varias sedes (casa madre + casas provinciales)
    #   - Sedes sin inmueble registrado aún (inmueble_id nullable)
    #   - Histórico temporal (vigente_desde / vigente_hasta)

    op.create_table(
        'sedes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),

        # ── Quién ocupa ───────────────────────────────────────────────────────
        sa.Column(
            'entidad_religiosa_id',
            sa.String(36),
            sa.ForeignKey(f'{S}.entidades_religiosas.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),

        # ── Qué edificio ──────────────────────────────────────────────────────
        # Nullable: sede conocida pero el inmueble aún no está registrado
        sa.Column(
            'inmueble_id',
            sa.String(36),
            sa.ForeignKey(f'{S}.inmuebles.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),

        # ── Tipo de sede ──────────────────────────────────────────────────────
        # DOMICILIO_SOCIAL: sede oficial registrada (RER / Catastro)
        # SEDE_OPERATIVA:   activa pero no registral
        # SEDE_HISTORICA:   pasada, ya no activa
        # OTRA:             almacén, colegio, hospital…
        sa.Column(
            'tipo_sede',
            sa.String(30),
            nullable=False,
            server_default='DOMICILIO_SOCIAL',
            index=True,
        ),

        # ── Temporalidad ──────────────────────────────────────────────────────
        sa.Column('vigente_desde', sa.Date, nullable=True, index=True),
        sa.Column('vigente_hasta', sa.Date, nullable=True, index=True),

        # ── Dirección (cuando no hay inmueble vinculado aún) ──────────────────
        sa.Column('nombre_via',    sa.String(255), nullable=True),
        sa.Column('numero_via',    sa.String(50),  nullable=True),
        sa.Column('codigo_postal', sa.String(10),  nullable=True),
        sa.Column(
            'municipio_id',
            sa.String(36),
            sa.ForeignKey(f'{S}.municipios.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),

        # ── Auditoría ─────────────────────────────────────────────────────────
        sa.Column('created_at',    sa.DateTime, nullable=False),
        sa.Column('updated_at',    sa.DateTime, nullable=True),
        sa.Column('deleted_at',    sa.DateTime, nullable=True),
        sa.Column('created_by_id', sa.String(36), nullable=True),
        sa.Column('updated_by_id', sa.String(36), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), nullable=True),

        schema=S,
    )

    op.create_index('ix_sedes_entidad_tipo',  'sedes', ['entidad_religiosa_id', 'tipo_sede'], schema=S)
    op.create_index('ix_sedes_vigencia',       'sedes', ['vigente_desde', 'vigente_hasta'],    schema=S)


def downgrade() -> None:
    op.drop_index('ix_sedes_vigencia',      table_name='sedes', schema=S)
    op.drop_index('ix_sedes_entidad_tipo',  table_name='sedes', schema=S)
    op.drop_table('sedes', schema=S)

    op.drop_index('ix_er_parroquia_id',  table_name='entidades_religiosas', schema=S)
    op.drop_index('ix_er_subtipo',       table_name='entidades_religiosas', schema=S)
    op.drop_index('ix_er_tipo_canonico', table_name='entidades_religiosas', schema=S)
    op.drop_column('entidades_religiosas', 'parroquia_id',  schema=S)
    op.drop_column('entidades_religiosas', 'subtipo',       schema=S)
    op.drop_column('entidades_religiosas', 'tipo_canonico', schema=S)
