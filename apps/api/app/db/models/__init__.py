# -*- coding: utf-8 -*-
"""MODELO ÚNICO: este paquete ya no define modelos.

Re-exporta el modelo canónico de sipi-core (packages/sipi-core). Cualquier
cambio de modelo se hace ALLÍ; las migraciones viven en sipi-core/alembic.
"""
from sipi_core.db.registry import Base  # noqa: F401
from sipi_core.mixins import UUIDPKMixin, AuditMixin  # noqa: F401
from sipi_core import models as _core_models
from sipi_core.models import *  # noqa: F401,F403

__all__ = [n for n in dir(_core_models) if not n.startswith("_")]
