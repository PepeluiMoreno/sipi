"""Añadir provincias_eclesiasticas, parroquias y campos CEE a diocesis

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-03-20

Modela la jerarquía eclesiástica española:
  ProvinciaEclesiastica (13) → Diocesis/Archidiocesis (70) → Parroquia (~23000)
  La Parroquia es el nodo de unión entre la jerarquía católica y la geográfica INE
  (municipio_id → sipi.municipios).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Columnas nuevas en diocesis ───────────────────────────────────────────
    op.add_column('diocesis',
        sa.Column('es_archidiocesis', sa.Boolean(), nullable=False, server_default='false'),
        schema='sipi')
    op.add_column('diocesis',
        sa.Column('cee_slug', sa.String(100), nullable=True),
        schema='sipi')
    op.add_column('diocesis',
        sa.Column('sitio_web_propio', sa.String(500), nullable=True),
        schema='sipi')
    op.add_column('diocesis',
        sa.Column('obispo_nombre', sa.String(200), nullable=True),
        schema='sipi')
    op.add_column('diocesis',
        sa.Column('obispo_foto_url', sa.String(500), nullable=True),
        schema='sipi')
    op.create_unique_constraint('uq_diocesis_cee_slug', 'diocesis', ['cee_slug'], schema='sipi')
    op.create_index('ix_sipi_diocesis_cee_slug', 'diocesis', ['cee_slug'], schema='sipi')

    # ── Tabla provincias_eclesiasticas ────────────────────────────────────────
    op.create_table(
        'provincias_eclesiasticas',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('nombre', sa.String(150), nullable=False),
        sa.Column('wikidata_qid', sa.String(32), nullable=True),
        sa.Column('sede_metropolitana_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(36), nullable=True),
        sa.Column('updated_by_id', sa.String(36), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['sede_metropolitana_id'], ['sipi.diocesis.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['sipi.usuarios.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['sipi.usuarios.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['sipi.usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
        sa.UniqueConstraint('wikidata_qid'),
        schema='sipi',
    )
    op.create_index('ix_sipi_prov_ecl_nombre', 'provincias_eclesiasticas', ['nombre'], schema='sipi')
    op.create_index('ix_sipi_prov_ecl_sede', 'provincias_eclesiasticas', ['sede_metropolitana_id'], schema='sipi')

    # ── FK provincia_eclesiastica_id en diocesis ──────────────────────────────
    op.add_column('diocesis',
        sa.Column('provincia_eclesiastica_id', sa.String(36), nullable=True),
        schema='sipi')
    op.create_foreign_key(
        'diocesis_provincia_eclesiastica_id_fkey', 'diocesis',
        'provincias_eclesiasticas', ['provincia_eclesiastica_id'], ['id'],
        source_schema='sipi', referent_schema='sipi')
    op.create_index('ix_sipi_diocesis_prov_ecl', 'diocesis', ['provincia_eclesiastica_id'], schema='sipi')

    # ── Tabla parroquias ──────────────────────────────────────────────────────
    op.create_table(
        'parroquias',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('titular', sa.String(255), nullable=True),
        sa.Column('diocesis_id', sa.String(36), nullable=True),
        sa.Column('municipio_id', sa.String(36), nullable=True),
        sa.Column('nombre_via', sa.String(255), nullable=True),
        sa.Column('codigo_postal', sa.String(10), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('cee_url_diocesis', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(36), nullable=True),
        sa.Column('updated_by_id', sa.String(36), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['diocesis_id'], ['sipi.diocesis.id']),
        sa.ForeignKeyConstraint(['municipio_id'], ['sipi.municipios.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['sipi.usuarios.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['sipi.usuarios.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['sipi.usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='sipi',
    )
    op.create_index('ix_sipi_parroquias_nombre', 'parroquias', ['nombre'], schema='sipi')
    op.create_index('ix_sipi_parroquias_diocesis_id', 'parroquias', ['diocesis_id'], schema='sipi')
    op.create_index('ix_sipi_parroquias_municipio_id', 'parroquias', ['municipio_id'], schema='sipi')
    op.create_index('ix_sipi_parroquias_cp', 'parroquias', ['codigo_postal'], schema='sipi')


def downgrade() -> None:
    op.drop_table('parroquias', schema='sipi')
    op.drop_column('diocesis', 'provincia_eclesiastica_id', schema='sipi')
    op.drop_table('provincias_eclesiasticas', schema='sipi')
    op.drop_column('diocesis', 'obispo_foto_url', schema='sipi')
    op.drop_column('diocesis', 'obispo_nombre', schema='sipi')
    op.drop_column('diocesis', 'sitio_web_propio', schema='sipi')
    op.drop_column('diocesis', 'cee_slug', schema='sipi')
    op.drop_column('diocesis', 'es_archidiocesis', schema='sipi')
