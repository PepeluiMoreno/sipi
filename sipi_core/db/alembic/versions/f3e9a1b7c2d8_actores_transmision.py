"""Tablas transmitentes y adquirientes para actores de transmisiones

Revision ID: f3e9a1b7c2d8
Revises: 88d33911b427
Create Date: 2026-03-18

Añade:
- app.transmitentes — vendedores/cedentes (polimórficos: entidad religiosa, administración, privado)
- app.adquirientes  — compradores/adquirientes (idem)
- FKs en app.transmisiones → transmitentes y adquirientes
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f3e9a1b7c2d8'
down_revision: Union[str, None] = '88d33911b427'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'app'


def upgrade() -> None:
    # --- Tabla transmitentes ---
    op.create_table(
        'transmitentes',
        # PK + audit
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.usuarios.id'), nullable=True),
        sa.Column('updated_by_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.usuarios.id'), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.usuarios.id'), nullable=True),
        # Identificación (IdentificacionMixin)
        sa.Column('tipo_identificacion', sa.String(50), nullable=True),
        sa.Column('identificacion', sa.String(50), nullable=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('apellidos', sa.String(200), nullable=True),
        sa.Column('identificacion_extranjera', sa.String(50), nullable=True),
        # Contacto/Dirección (ContactoDireccionMixin)
        sa.Column('municipio_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.municipios.id'), nullable=True),
        sa.Column('provincia_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.provincias.id'), nullable=True),
        sa.Column('comunidad_autonoma_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.comunidades_autonomas.id'), nullable=True),
        sa.Column('tipo_via_id', sa.String(36), nullable=True),
        sa.Column('direccion', sa.String(500), nullable=True),
        sa.Column('codigo_postal', sa.String(10), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('latitud', sa.Float(), nullable=True),
        sa.Column('longitud', sa.Float(), nullable=True),
        # Polimorfismo
        sa.Column('tipo_actor', sa.String(50), nullable=True, index=True),
        sa.Column('actor_ref_id', sa.String(36), nullable=True, index=True),
        schema=SCHEMA,
    )
    op.create_index('ix_transmitentes_identificacion', 'transmitentes', ['identificacion'], schema=SCHEMA)
    op.create_index('ix_transmitentes_nombre', 'transmitentes', ['nombre'], schema=SCHEMA)

    # --- Tabla adquirientes ---
    op.create_table(
        'adquirientes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.usuarios.id'), nullable=True),
        sa.Column('updated_by_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.usuarios.id'), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.usuarios.id'), nullable=True),
        sa.Column('tipo_identificacion', sa.String(50), nullable=True),
        sa.Column('identificacion', sa.String(50), nullable=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('apellidos', sa.String(200), nullable=True),
        sa.Column('identificacion_extranjera', sa.String(50), nullable=True),
        sa.Column('municipio_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.municipios.id'), nullable=True),
        sa.Column('provincia_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.provincias.id'), nullable=True),
        sa.Column('comunidad_autonoma_id', sa.String(36), sa.ForeignKey(f'{SCHEMA}.comunidades_autonomas.id'), nullable=True),
        sa.Column('tipo_via_id', sa.String(36), nullable=True),
        sa.Column('direccion', sa.String(500), nullable=True),
        sa.Column('codigo_postal', sa.String(10), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('latitud', sa.Float(), nullable=True),
        sa.Column('longitud', sa.Float(), nullable=True),
        sa.Column('tipo_actor', sa.String(50), nullable=True, index=True),
        sa.Column('actor_ref_id', sa.String(36), nullable=True, index=True),
        schema=SCHEMA,
    )
    op.create_index('ix_adquirientes_identificacion', 'adquirientes', ['identificacion'], schema=SCHEMA)
    op.create_index('ix_adquirientes_nombre', 'adquirientes', ['nombre'], schema=SCHEMA)

    # --- FKs en transmisiones ---
    op.add_column('transmisiones',
        sa.Column('transmitente_id', sa.String(36), nullable=True),
        schema=SCHEMA,
    )
    op.add_column('transmisiones',
        sa.Column('adquiriente_id', sa.String(36), nullable=True),
        schema=SCHEMA,
    )
    op.create_index('ix_transmisiones_transmitente_id', 'transmisiones', ['transmitente_id'], schema=SCHEMA)
    op.create_index('ix_transmisiones_adquiriente_id', 'transmisiones', ['adquiriente_id'], schema=SCHEMA)
    op.create_foreign_key(
        'fk_transmisiones_transmitente', 'transmisiones', 'transmitentes',
        ['transmitente_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA,
    )
    op.create_foreign_key(
        'fk_transmisiones_adquiriente', 'transmisiones', 'adquirientes',
        ['adquiriente_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint('fk_transmisiones_adquiriente', 'transmisiones', schema=SCHEMA, type_='foreignkey')
    op.drop_constraint('fk_transmisiones_transmitente', 'transmisiones', schema=SCHEMA, type_='foreignkey')
    op.drop_index('ix_transmisiones_adquiriente_id', table_name='transmisiones', schema=SCHEMA)
    op.drop_index('ix_transmisiones_transmitente_id', table_name='transmisiones', schema=SCHEMA)
    op.drop_column('transmisiones', 'adquiriente_id', schema=SCHEMA)
    op.drop_column('transmisiones', 'transmitente_id', schema=SCHEMA)

    op.drop_index('ix_adquirientes_nombre', table_name='adquirientes', schema=SCHEMA)
    op.drop_index('ix_adquirientes_identificacion', table_name='adquirientes', schema=SCHEMA)
    op.drop_table('adquirientes', schema=SCHEMA)

    op.drop_index('ix_transmitentes_nombre', table_name='transmitentes', schema=SCHEMA)
    op.drop_index('ix_transmitentes_identificacion', table_name='transmitentes', schema=SCHEMA)
    op.drop_table('transmitentes', schema=SCHEMA)
