# -*- coding: utf-8 -*-
"""Pipeline de consumo: por cada recurso ODM mapeado, resuelve sus registros
sobre sipi-core en lotes. Los inmuebles OSM/CEE se derivan al módulo de fusión.
"""
from __future__ import annotations

import logging
from collections import Counter

from . import config
from .client import ODMClient
from .resolvers import RESOLVERS, RESOLVERS_INMUEBLE_DIRECTO

log = logging.getLogger("sipi.etl.odm")


async def poblar_recurso(session_factory, client: ODMClient, resource_name: str,
                         destino: tuple | None = None) -> Counter:
    """Puebla sipi-core desde un recurso ODM. `session_factory` es un callable
    que devuelve un async context manager de AsyncSession (sipi-core).

    `destino` = (dominio, fuente) ya resuelto (p. ej. por colección desde el
    webhook). Si es None, se resuelve por `RESOURCE_MAP` (backfill por nombre)."""
    if destino is None:
        if resource_name not in config.RESOURCE_MAP:
            raise ValueError(f"Recurso no mapeado en RESOURCE_MAP: {resource_name!r}")
        destino = config.RESOURCE_MAP[resource_name]
    dominio, fuente = destino
    stats = Counter()

    # Inmuebles OSM/CEE -> fusión (no upsert directo)
    if dominio == "inmueble" and fuente not in RESOLVERS_INMUEBLE_DIRECTO:
        n = await feed_fusion(client, resource_name, fuente)
        stats[f"fusion:{fuente}"] += n
        return stats

    resolver = (
        RESOLVERS_INMUEBLE_DIRECTO[fuente]
        if dominio == "inmueble"
        else RESOLVERS[dominio]
    )

    batch = 0
    async with session_factory() as session:
        for rec in client.iter_resource(resource_name):
            action = await resolver(session, rec, fuente)
            stats[action] += 1
            batch += 1
            if batch >= config.BATCH_SIZE:
                await session.commit()
                batch = 0
        await session.commit()
    log.info("Recurso %s -> %s", resource_name, dict(stats))
    return stats


async def feed_fusion(client: ODMClient, resource_name: str, fuente: str) -> int:
    """Vuelca un recurso de inmuebles (OSM o CEE) a la entrada del módulo de
    fusión. La fusión (modules/fusion) deduplica CEE×OSM por municipio y emite
    el seed + hallazgos. Aquí solo materializamos el JSONL de ODM al formato que
    espera sources.load_osm / load_cee, sin reextraer nada."""
    import json
    import tempfile

    path = tempfile.mktemp(prefix=f"odm_{fuente.lower()}_", suffix=".jsonl")
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for rec in client.iter_resource(resource_name):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    log.info("Recurso %s materializado para fusión en %s (%d registros)", resource_name, path, n)
    # NB: el orquestador de fusión (modules.fusion.seed.run_fusion) se invoca una
    # vez se han materializado AMBAS caras (CEE y OSM). El acoplamiento exacto a
    # sources.load_* se cierra cuando se confirme el esquema JSONL de cada recurso.
    return n


async def poblar_todo(session_factory, client: ODMClient = None) -> Counter:
    """Backfill completo: recorre todos los recursos mapeados en orden de
    dependencia (agentes antes que inmuebles, para que las FK resuelvan)."""
    client = client or ODMClient()
    total = Counter()
    orden = sorted(
        config.RESOURCE_MAP.items(),
        key=lambda kv: 0 if kv[1][0] != "inmueble" else 1,  # agentes primero
    )
    for resource_name, _ in orden:
        try:
            total.update(await poblar_recurso(session_factory, client, resource_name))
        except Exception as e:  # noqa: BLE001
            log.error("Fallo poblando %s: %s", resource_name, e)
            total[f"error:{resource_name}"] += 1
    return total
