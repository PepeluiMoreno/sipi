"""
config.py — Configuración del ETL de SIPI

Extiende sipi_core.config.Settings añadiendo el .env local del ETL
(DATABASE_URL apunta a localhost:5433 para acceso desde el host).

Uso:
    from config import get_settings, dsn

    s = get_settings()
    conn = await asyncpg.connect(dsn())
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict
from sipi_core.config import Settings

_ETL  = Path(__file__).parent   # SIPI-ETL/
_ROOT = _ETL.parent              # SIPI/


class ETLSettings(Settings):
    """Settings con override local para el ETL.

    Orden de carga (mayor precedencia al final):
      1. SIPI/.env           — config base compartida
      2. SIPI-ETL/.env       — DATABASE_URL para acceso desde el host
      3. Variables de entorno del sistema
    """
    model_config = SettingsConfigDict(
        env_file=[str(_ROOT / ".env"), str(_ETL / ".env")],
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> ETLSettings:
    return ETLSettings()


# ── Compatibilidad con scripts que usan cfg()/dsn() ──────────────────────────

def dsn() -> str:
    """DATABASE_URL lista para asyncpg directo."""
    return get_settings().sync_dsn


def cfg(key: str, default: str | None = None) -> str:
    """Lee una variable de configuración por nombre."""
    import os
    val = os.environ.get(key, default)
    if val is None:
        raise KeyError(f"Variable de entorno no definida: '{key}'")
    return val
