#!/usr/bin/env python3
"""Seed idempotente de procesos de vigilancia de portales inmobiliarios.

Un proceso = UN portal. Crea/actualiza un ProcesoVigilancia (tipo
portal_inmobiliario) por cada portal, con parámetros adecuados para detectar
inmuebles potencialmente inmatriculados (conventos, palacios episcopales,
ermitas…). Los selectores son un punto de partida (afinables desde la UI).

Fotocasa funciona vía httpx+bs4 (selectores verificados del recurso de ODM).
Idealista necesita render JS (anti-bot DataDome) → motor de survey/Selenium:
se deja el proceso INACTIVO hasta cablear ese motor.

Uso:  python -m sipi_core.scripts.seed_vigilancia
"""
import asyncio
from sqlalchemy import select

COMUN = {
    "umbral_score": 60,
    "keywords_inclusion": [
        "convento", "monasterio", "ermita", "iglesia", "palacio episcopal",
        "casa rectoral", "casa parroquial", "abadía", "santuario", "ábside",
        "espadaña", "claustro", "capilla", "priorato", "cenobio", "cartuja",
        "colegiata", "retablo", "sacristía",
    ],
    "keywords_exclusion": [
        "obra nueva", "promoción", "garaje", "plaza de aparcamiento",
        "chalet adosado", "parking", "trastero", "ático", "estudio",
        "local comercial", "nave industrial", "piso de",
    ],
    "tipologias": [
        "convento", "monasterio", "ermita", "iglesia", "palacio",
        "casa señorial", "abadía", "santuario", "colegiata", "casa rectoral",
    ],
}

SEEDS = [
    {
        "nombre": "Fotocasa — inmuebles religiosos",
        "frecuencia_cron": "0 7 * * *",
        "activo": True,
        "descripcion": "Anuncios de venta en Fotocasa potencialmente inmatriculados.",
        # Selectores verificados del recurso Fotocasa que funcionaba en ODM
        # (requests+bs4, sin Selenium). Fotocasa es parcialmente SSR.
        "fuente": {
            "id": "fotocasa", "nombre": "Fotocasa", "fetcher": "html_paginated", "activa": True,
            "params": {
                "url_busqueda": "https://www.fotocasa.es/es/comprar/viviendas/espana/todas-las-zonas/l",
                "selector_item": "article",
                "selector_titulo": "h3",
                "selector_precio": "[class*='text-display-3'] span",
                "selector_url": "h3 a",
                "selector_siguiente": "a[aria-label='Página siguiente']",
            },
        },
    },
    {
        "nombre": "Idealista — inmuebles religiosos",
        "frecuencia_cron": "0 7 * * *",
        "activo": False,  # anti-bot DataDome → requiere motor de survey (Selenium+stealth)
        "descripcion": "Anuncios de venta en Idealista (caserones y palacios). Requiere render JS.",
        "fuente": {
            "id": "idealista", "nombre": "Idealista", "fetcher": "html_paginated", "activa": True,
            "params": {
                "url_busqueda": "https://www.idealista.com/venta-viviendas/espana/con-tipos-de-vivienda_caserones-y-palacios/",
                "selector_item": "main.listing-items article",
                "selector_titulo": "a.item-link",
                "selector_precio": "span.item-price",
                "selector_url": "a.item-link",
                "selector_siguiente": "a.icon-arrow-right-after",
            },
        },
    },
    {
        "nombre": "Milanuncios — inmuebles religiosos",
        "frecuencia_cron": "0 7 * * *",
        "activo": False,
        "descripcion": "Anuncios de venta en Milanuncios. Afinar selectores antes de activar.",
        "fuente": {
            "id": "milanuncios", "nombre": "Milanuncios", "fetcher": "html_paginated", "activa": True,
            "params": {
                "url_busqueda": "https://www.milanuncios.com/venta-de-casas-y-chalets/",
                "selector_item": "article.ma-AdCardV2",
                "selector_titulo": ".ma-AdCardV2-title",
                "selector_precio": ".ma-AdPrice-value",
                "selector_url": "a.ma-AdCardV2-link",
                "selector_siguiente": ".sui-MoleculePagination-item--next a",
            },
        },
    },
]


async def _upsert(session, s) -> str:
    from sipi_core.models import ProcesoVigilancia
    proc = (await session.execute(
        select(ProcesoVigilancia).where(ProcesoVigilancia.nombre == s["nombre"])
    )).scalar_one_or_none()
    creado = proc is None
    if proc is None:
        proc = ProcesoVigilancia(nombre=s["nombre"], tipo="portal_inmobiliario")
        session.add(proc)
    proc.tipo = "portal_inmobiliario"
    proc.activo = s["activo"]
    proc.frecuencia_cron = s["frecuencia_cron"]
    proc.severidad_defecto = "aviso"
    proc.descripcion = s["descripcion"]
    proc.parametros = {**COMUN, "fuente": s["fuente"]}
    return f"{'creado' if creado else 'actualizado'}: {s['nombre']}"


async def main():
    from sipi_core.db.sessions import AsyncDatabaseManager
    mgr = AsyncDatabaseManager()
    async with mgr.session() as session:
        for s in SEEDS:
            print("Seed vigilancia", await _upsert(session, s))
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
