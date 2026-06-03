"""Crear entidades_religiosas completa con campos RER

Revision ID: f4g5h6i7j8k9
Revises: e1f2a3b4c5d6
Create Date: 2026-03-20

Crea:
  - sipi.tipos_entidad_religiosa  — catálogo de tipos (PARROQUIA, ORDEN, COMUNIDAD…)
  - sipi.entidades_religiosas     — todas las entidades del RER + campos de clasificación
  - sipi.entidades_religiosas_titulares — histórico de representantes

Campos RER añadidos:
  seccion          GENERAL | ESPECIAL (Especial = exclusivamente católicas)
  confesion        CATÓLICOS | EVANGÉLICOS | ISLAM | JUDÍOS | BUDISTAS…
  fecha_inscripcion_rer  fecha de alta en el RER
  es_territorial   True si ligada a territorio (parroquia, diócesis)
  diocesis_id      FK a sipi.diocesis (solo entidades católicas)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f4g5h6i7j8k9'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = 'sipi'


def upgrade() -> None:
    # ── tipos_entidad_religiosa ───────────────────────────────────────────────
    op.create_table(
        'tipos_entidad_religiosa',
        sa.Column('id',          sa.String(36),  primary_key=True),
        sa.Column('codigo',      sa.String(50),  nullable=False, unique=True),
        sa.Column('nombre',      sa.String(150), nullable=False),
        sa.Column('descripcion', sa.Text(),      nullable=True),
        sa.Column('activo',      sa.Boolean(),   nullable=False, server_default='true'),
        sa.Column('created_at',  sa.DateTime(),  nullable=False),
        sa.Column('updated_at',  sa.DateTime(),  nullable=True),
        sa.Column('deleted_at',  sa.DateTime(),  nullable=True),
        sa.Column('created_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('updated_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('created_from_ip', sa.String(45), nullable=True),
        sa.Column('updated_from_ip', sa.String(45), nullable=True),
        schema=S,
    )
    op.create_index('ix_tipo_entidad_religiosa_codigo', 'tipos_entidad_religiosa', ['codigo'], schema=S)

    # ── entidades_religiosas ──────────────────────────────────────────────────
    op.create_table(
        'entidades_religiosas',
        # PK + audit
        sa.Column('id',          sa.String(36),  primary_key=True),
        sa.Column('created_at',  sa.DateTime(),  nullable=False),
        sa.Column('updated_at',  sa.DateTime(),  nullable=True),
        sa.Column('deleted_at',  sa.DateTime(),  nullable=True),
        sa.Column('created_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('updated_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('created_from_ip', sa.String(45), nullable=True),
        sa.Column('updated_from_ip', sa.String(45), nullable=True),
        # IdentificacionMixin
        sa.Column('tipo_identificacion', sa.String(20),  nullable=True),
        sa.Column('identificacion',      sa.String(50),  nullable=True, index=True),
        sa.Column('nombre',              sa.String(255), nullable=False),
        sa.Column('apellidos',           sa.String(200), nullable=True),
        sa.Column('identificacion_extranjera', sa.String(50), nullable=True),
        # ContactoMixin
        sa.Column('email_personal',   sa.String(255), nullable=True),
        sa.Column('email_corporativo', sa.String(255), nullable=True),
        sa.Column('telefono',         sa.String(20),  nullable=True),
        sa.Column('telefono_movil',   sa.String(20),  nullable=True),
        sa.Column('fax',              sa.String(20),  nullable=True),
        sa.Column('sitio_web',        sa.String(500), nullable=True),
        sa.Column('notas',            sa.String(500), nullable=True),
        # DireccionMixin
        sa.Column('tipo_via_id',    sa.String(36),  nullable=True),
        sa.Column('nombre_via',     sa.String(255), nullable=True),
        sa.Column('numero',         sa.String(10),  nullable=True),
        sa.Column('bloque',         sa.String(10),  nullable=True),
        sa.Column('escalera',       sa.String(10),  nullable=True),
        sa.Column('piso',           sa.String(10),  nullable=True),
        sa.Column('puerta',         sa.String(10),  nullable=True),
        sa.Column('codigo_postal',  sa.String(10),  nullable=True),
        sa.Column('comunidad_autonoma_id', sa.String(36),
                  sa.ForeignKey('sipi.comunidades_autonomas.id'), nullable=True),
        sa.Column('provincia_id', sa.String(36),
                  sa.ForeignKey('sipi.provincias.id'), nullable=True),
        sa.Column('municipio_id', sa.String(36),
                  sa.ForeignKey('sipi.municipios.id'), nullable=True),
        sa.Column('latitud',  sa.Float(), nullable=True),
        sa.Column('longitud', sa.Float(), nullable=True),
        # Campos propios RER
        sa.Column('numero_registro', sa.String(50), nullable=False, unique=True),
        sa.Column('seccion',          sa.String(20),  nullable=True),
        sa.Column('confesion',        sa.String(100), nullable=True),
        sa.Column('fecha_inscripcion_rer', sa.DateTime(), nullable=True),
        sa.Column('fecha_fundacion',  sa.DateTime(), nullable=True),
        sa.Column('activa',           sa.Boolean(),  nullable=False, server_default='true'),
        sa.Column('es_territorial',   sa.Boolean(),  nullable=False, server_default='false'),
        # FK eclesiástica
        sa.Column('diocesis_id', sa.String(36),
                  sa.ForeignKey('sipi.diocesis.id'), nullable=True),
        # FK tipología
        sa.Column('tipo_entidad_id', sa.String(36),
                  sa.ForeignKey('sipi.tipos_entidad_religiosa.id', ondelete='RESTRICT'),
                  nullable=True),
        schema=S,
    )
    op.create_index('ix_entidad_religiosa_numero_registro', 'entidades_religiosas', ['numero_registro'], schema=S)
    op.create_index('ix_entidad_religiosa_nombre',     'entidades_religiosas', ['nombre'],     schema=S)
    op.create_index('ix_entidad_religiosa_seccion',    'entidades_religiosas', ['seccion'],    schema=S)
    op.create_index('ix_entidad_religiosa_confesion',  'entidades_religiosas', ['confesion'],  schema=S)
    op.create_index('ix_entidad_religiosa_diocesis',   'entidades_religiosas', ['diocesis_id'], schema=S)
    op.create_index('ix_entidad_religiosa_municipio',  'entidades_religiosas', ['municipio_id'], schema=S)
    op.create_index('ix_entidad_religiosa_codigo_postal', 'entidades_religiosas', ['codigo_postal'], schema=S)

    # ── entidades_religiosas_titulares ────────────────────────────────────────
    op.create_table(
        'entidades_religiosas_titulares',
        sa.Column('id',         sa.String(36),  primary_key=True),
        sa.Column('created_at', sa.DateTime(),  nullable=False),
        sa.Column('updated_at', sa.DateTime(),  nullable=True),
        sa.Column('deleted_at', sa.DateTime(),  nullable=True),
        sa.Column('created_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('updated_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), sa.ForeignKey('sipi.usuarios.id'), nullable=True),
        sa.Column('created_from_ip', sa.String(45), nullable=True),
        sa.Column('updated_from_ip', sa.String(45), nullable=True),
        # IdentificacionMixin
        sa.Column('tipo_identificacion', sa.String(20),  nullable=True),
        sa.Column('identificacion',      sa.String(50),  nullable=True),
        sa.Column('nombre',              sa.String(255), nullable=False),
        sa.Column('apellidos',           sa.String(200), nullable=True),
        sa.Column('identificacion_extranjera', sa.String(50), nullable=True),
        # FK a la entidad
        sa.Column('entidad_religiosa_id', sa.String(36),
                  sa.ForeignKey('sipi.entidades_religiosas.id', ondelete='CASCADE'),
                  nullable=False),
        # Periodo de cargo
        sa.Column('cargo',      sa.String(100), nullable=True),
        sa.Column('fecha_inicio', sa.DateTime(), nullable=True),
        sa.Column('fecha_fin',    sa.DateTime(), nullable=True),
        schema=S,
    )
    op.create_index('ix_ert_entidad', 'entidades_religiosas_titulares', ['entidad_religiosa_id'], schema=S)


def downgrade() -> None:
    op.drop_table('entidades_religiosas_titulares', schema=S)
    op.drop_table('entidades_religiosas', schema=S)
    op.drop_table('tipos_entidad_religiosa', schema=S)
