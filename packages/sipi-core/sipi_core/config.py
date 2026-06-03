"""
sipi_core/config.py — Configuración centralizada SIPI

Todos los módulos Python (SIPI-API, SIPI-ETL, SIPI-WATCHERS) importan desde aquí.
Carga automática desde el root del proyecto (SIPI/.env).
Las variables de entorno del sistema tienen prioridad sobre el archivo .env.

Uso:
    from sipi_core.config import get_settings
    s = get_settings()
    print(s.database_url)
    print(s.sync_dsn)   # para asyncpg directo
"""

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# SIPI-CORE/sipi_core/ -> SIPI-CORE/ -> SIPI/
_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
    )

    # Base de datos
    database_url: str = "postgresql+asyncpg://sipi:sipi@localhost:5432/sipi"
    database_schema: str = "sipi"
    defined_schemas: str = "sipi"

    # GraphQL
    graphql_host: str = "0.0.0.0"
    graphql_port: int = 8040
    graphql_max_depth: int = 10

    # SQLAlchemy
    sqlalchemy_echo: bool = False
    pool_size: int = 20
    pool_max_overflow: int = 10
    pool_timeout: int = 30

    # Entorno
    environment: str = "development"

    # MinIO
    minio_bucket: str = "sipi-media"
    minio_endpoint: str = "http://minio:9000"
    minio_endpoint_external: str = "http://localhost:9000"
    minio_root_user: str = "sipi"
    minio_root_password: str = "CHANGE_ME_IN_PRODUCTION"

    @computed_field
    @property
    def debug(self) -> bool:
        return self.environment == "development"

    @computed_field
    @property
    def sync_dsn(self) -> str:
        """URL para asyncpg directo (sin prefijo SQLAlchemy)."""
        return (
            self.database_url
            .replace("postgresql+asyncpg://", "postgresql://")
            .replace("postgresql+psycopg2://", "postgresql://")
        )

    @computed_field
    @property
    def async_dsn(self) -> str:
        """URL normalizada para SQLAlchemy async."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Singleton con cache. En tests: get_settings.cache_clear() para reiniciar."""
    return Settings()
