#!/usr/bin/env python3
"""Seed idempotente de un proceso de vigilancia de portales inmobiliarios.

Crea/actualiza un ProcesoVigilancia (tipo portal_inmobiliario) con fuentes reales
de portales españoles y parámetros adecuados para detectar inmuebles potencialmente
inmatriculados (conventos, palacios episcopales, ermitas…). Los selectores son un
punto de partida razonable; se afinan desde la UI.

Uso:  python -m sipi_core.scripts.seed_vigilancia
"""
import asyncio
from sqlalchemy import select

SEED = {
    "nombre": "Inmuebles religiosos en venta (portales)",
    "frecuencia_cron": "0 7 * * *",   # cada día a las 7:00
    "descripcion": "Detecta anuncios de venta de inmuebles potencialmente inmatriculados "
                   "(conventos, monasterios, ermitas, palacios episcopales, casas rectorales…).",
    "parametros": {
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
        "fuentes": [
            {
                "id": "idealista-caserones-palacios",
                "nombre": "Idealista — caserones y palacios",
                "fetcher": "html_paginated",
                "activa": False,  # anti-bot DataDome → requiere motor de survey (Selenium+stealth)
                "params": {
                    "url_busqueda": "https://www.idealista.com/venta-viviendas/espana/con-tipos-de-vivienda_caserones-y-palacios/",
                    "selector_item": "article.item",
                    "selector_titulo": "a.item-link",
                    "selector_precio": "span.item-price",
                    "selector_url": "a.item-link",
                    "selector_siguiente": "a.icon-arrow-right-after",
                },
            },
            {
                "id": "idealista-edificios",
                "nombre": "Idealista — edificios",
                "fetcher": "html_paginated",
                "activa": False,  # anti-bot DataDome → requiere motor de survey (Selenium+stealth)
                "params": {
                    "url_busqueda": "https://www.idealista.com/venta-edificios/espana/",
                    "selector_item": "article.item",
                    "selector_titulo": "a.item-link",
                    "selector_precio": "span.item-price",
                    "selector_url": "a.item-link",
                    "selector_siguiente": "a.icon-arrow-right-after",
                },
            },
            {
                # Selectores verificados del recurso Fotocasa que funcionaba en ODM
                # (requests + bs4, sin Selenium). record=article; h3 (título/enlace);
                # precio en [class*=text-display-3] span. Ver opendatamanager/seed_resources.py.
                "id": "fotocasa-viviendas",
                "nombre": "Fotocasa — viviendas",
                "fetcher": "html_paginated",
                "activa": True,
                "params": {
                    "url_busqueda": "https://www.fotocasa.es/es/comprar/viviendas/espana/todas-las-zonas/l",
                    "selector_item": "article",
                    "selector_titulo": "h3",
                    "selector_precio": "[class*='text-display-3'] span",
                    "selector_url": "h3 a",
                    "selector_siguiente": "a[aria-label='Página siguiente']",
                },
            },
            {
                "id": "milanuncios-casas",
                "nombre": "Milanuncios — casas y chalets",
                "fetcher": "html_paginated",
                "activa": False,
                "params": {
                    "url_busqueda": "https://www.milanuncios.com/venta-de-casas-y-chalets/",
                    "selector_item": "article.ma-AdCardV2",
                    "selector_titulo": ".ma-AdCardV2-title",
                    "selector_precio": ".ma-AdPrice-value",
                    "selector_url": "a.ma-AdCardV2-link",
                    "selector_siguiente": ".sui-MoleculePagination-item--next a",
                },
            },
        ],
    },
}


async def seed(session) -> str:
    from sipi_core.models import ProcesoVigilancia
    proc = (await session.execute(
        select(ProcesoVigilancia).where(ProcesoVigilancia.nombre == SEED["nombre"])
    )).scalar_one_or_none()
    creado = proc is None
    if proc is None:
        proc = ProcesoVigilancia(nombre=SEED["nombre"], tipo="portal_inmobiliario")
        session.add(proc)
    proc.tipo = "portal_inmobiliario"
    proc.activo = True
    proc.frecuencia_cron = SEED["frecuencia_cron"]
    proc.severidad_defecto = "aviso"
    proc.descripcion = SEED["descripcion"]
    proc.parametros = SEED["parametros"]
    await session.commit()
    return f"{'creado' if creado else 'actualizado'}: {proc.id}"


async def main():
    from sipi_core.db.sessions import AsyncDatabaseManager
    mgr = AsyncDatabaseManager()
    async with mgr.session() as session:
        print("Seed vigilancia portales", await seed(session))


if __name__ == "__main__":
    asyncio.run(main())
