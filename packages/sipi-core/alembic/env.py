from alembic import context
from sqlalchemy import engine_from_config, pool
import sipi_core.models  # registra todos los modelos
from sipi_core.db.registry import Base

config = context.config
target_metadata = Base.metadata

def _include(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        if name == "spatial_ref_sys":
            return False
        return getattr(obj, "schema", None) in ("app", "gis")
    return True

try:
    from geoalchemy2 import alembic_helpers
    _render = alembic_helpers.render_item
    _writer = getattr(alembic_helpers, 'writer', None)
    def include_object(obj, name, type_, reflected, compare_to):
        return alembic_helpers.include_object(obj, name, type_, reflected, compare_to) \
               and _include(obj, name, type_, reflected, compare_to)
except ImportError:
    _render = None
    _writer = None
    include_object = _include

def run_migrations_online():
    import os
    url = os.getenv("DATABASE_URL")
    if url:
        config.set_main_option("sqlalchemy.url", url)
    connectable = engine_from_config(config.get_section(config.config_ini_section),
                                     prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          include_schemas=True, include_object=include_object,
                          render_item=_render, process_revision_directives=_writer,
                          version_table_schema="app",
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
