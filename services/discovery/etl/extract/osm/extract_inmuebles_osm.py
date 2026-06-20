#!/usr/bin/env python3
"""
extract_inmuebles_osm.py — Sincronización de inmuebles religiosos desde OpenStreetMap

Extrae edificios religiosos católicos/cristianos de España desde la API Overpass
y los crea/actualiza en las tablas sipi.inmuebles + sipi.inmuebles_osm_ext.

Requiere ejecutar previamente 01_cargar_tipologias.py para que los catálogos
(tipos_inmueble, etc.) estén poblados.

Uso:
    # España completa:
    python scripts/extract_inmuebles_osm.py

    # Provincia específica:
    python scripts/extract_inmuebles_osm.py --provincia "Madrid"

    # Simulación sin guardar:
    python scripts/extract_inmuebles_osm.py --dry-run

    # España completa, sin simulación:
    python scripts/extract_inmuebles_osm.py --spain
"""

import asyncio
import json
import logging
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import httpx
from dotenv import load_dotenv
from shapely.geometry import Point

# ── Entorno ───────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "SIPI-CORE"))

from geoalchemy2.shape import from_shape
from sqlalchemy import select

from sipi_core.db.sessions import AsyncDatabaseManager
from sipi_core.modules.inmuebles.inmuebles import Inmueble, InmuebleOSMExt
from sipi_core.modules.catalogos.tipologias import TipoInmueble

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "SIPI-Heritage-System/1.0 (https://github.com/sipi)"

# Mapeo tags OSM → nombre en catálogo tipos_inmueble
OSM_TIPO_MAP = {
    "cathedral":      "Catedral",
    "basilica":       "Basílica",
    "church":         "Iglesia",
    "chapel":         "Capilla",
    "monastery":      "Monasterio",
    "convent":        "Convento",
    "hermitage":      "Ermita",
    "wayside_shrine": "Humilladero",
    "bell_tower":     "Campanario",
    "cross":          "Cruz",
    "wayside_cross":  "Crucero",
    "lourdes_grotto": "Gruta",
}


# ── Construcción de queries Overpass ──────────────────────────────────────────

def _overpass_spain() -> str:
    return """
    [out:json][timeout:1800];
    area["ISO3166-1"="ES"]->.es;
    (
      node["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"](area.es);
      way ["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"](area.es);
      rel ["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"](area.es);
      node["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"](area.es);
      way ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"](area.es);
      rel ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"](area.es);
      node["amenity"="place_of_worship"]["religion"="christian"][!"denomination"](area.es);
      way ["amenity"="place_of_worship"]["religion"="christian"][!"denomination"](area.es);
      node["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["religion"="christian"][!"denomination"](area.es);
      way ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["religion"="christian"][!"denomination"](area.es);
      node["place_of_worship"~"^(cross|wayside_shrine|lourdes_grotto)$"]["religion"="christian"](area.es);
      way ["place_of_worship"~"^(cross|wayside_shrine|lourdes_grotto)$"]["religion"="christian"](area.es);
    );
    out tags center qt;
    """


def _overpass_bbox(min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> str:
    bb = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    return f"""
    [out:json][timeout:180];
    (
      node["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"]({bb});
      way ["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"]({bb});
      node["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"]({bb});
      way ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"]({bb});
      node["amenity"="place_of_worship"]["religion"="christian"][!"denomination"]({bb});
      way ["amenity"="place_of_worship"]["religion"="christian"][!"denomination"]({bb});
      node["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["religion"="christian"][!"denomination"]({bb});
      node["place_of_worship"~"^(cross|wayside_shrine|lourdes_grotto)$"]["religion"="christian"]({bb});
    );
    out tags center qt;
    """


# ── Helpers ───────────────────────────────────────────────────────────────────

def _coords(element: dict) -> Tuple[Optional[float], Optional[float]]:
    if element.get("lat") and element.get("lon"):
        return element["lat"], element["lon"]
    if "center" in element:
        return element["center"].get("lat"), element["center"].get("lon")
    return None, None


def _infer_type(tags: dict) -> Optional[str]:
    building = tags.get("building")
    if building in OSM_TIPO_MAP:
        return building
    if tags.get("amenity") == "place_of_worship":
        return "place_of_worship"
    if pow_type := tags.get("place_of_worship"):
        return pow_type
    return None


def _build_address(tags: dict) -> Optional[str]:
    parts = [
        tags.get("addr:street", ""),
        tags.get("addr:housenumber", ""),
        tags.get("addr:postcode", "") and f"CP {tags['addr:postcode']}",
        tags.get("addr:city", ""),
    ]
    return ", ".join(p for p in parts if p) or None


def _build_description(tags: dict) -> Optional[str]:
    parts = []
    if d := tags.get("denomination"):   parts.append(f"Denominación: {d}")
    if a := tags.get("architect"):      parts.append(f"Arquitecto: {a}")
    if y := tags.get("start_date"):     parts.append(f"Construcción: {y}")
    if desc := tags.get("description"): parts.append(desc)
    return " | ".join(parts) or None


# ── Agente OSM ────────────────────────────────────────────────────────────────

class OSMSyncAgent:
    """Sincroniza iglesias/edificios religiosos de España desde Overpass OSM."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._tipo_cache: dict[str, str] = {}   # nombre → id

    # ── Fetch Overpass ────────────────────────────────────────────────────────

    async def fetch_elements(
        self,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        use_spain: bool = True,
    ) -> list[dict]:
        query = _overpass_spain() if use_spain else _overpass_bbox(*bbox)
        timeout = 1860.0 if use_spain else 180.0
        log.info("Consultando Overpass API… (puede tardar varios minutos para España completa)")
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(OVERPASS_URL, data={"data": query}, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
        elements = r.json().get("elements", [])
        log.info(f"  {len(elements)} elementos recibidos de OSM")
        return elements

    async def get_provincia_bbox(self, nombre: str) -> Optional[Tuple[float, float, float, float]]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{NOMINATIM_URL}/search",
                    params={"q": f"{nombre}, España", "format": "json", "limit": 1},
                    headers={"User-Agent": USER_AGENT},
                )
                results = r.json()
                if results:
                    bb = results[0].get("boundingbox")
                    return (float(bb[0]), float(bb[2]), float(bb[1]), float(bb[3]))
        except Exception as e:
            log.error(f"No se pudo obtener bbox para '{nombre}': {e}")
        return None

    # ── Procesado principal ───────────────────────────────────────────────────

    async def sync(
        self,
        bbox: Optional[Tuple] = None,
        use_spain: bool = True,
    ) -> dict:
        elements = await self.fetch_elements(bbox=bbox, use_spain=use_spain)
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        db = AsyncDatabaseManager()
        async with db.session() as session:
            # Precargar catálogo tipos_inmueble → cache nombre:id
            result = await session.execute(select(TipoInmueble))
            for tipo in result.scalars():
                self._tipo_cache[tipo.nombre] = tipo.id

            for i, element in enumerate(elements, 1):
                try:
                    result = await self._process(session, element)
                    stats[result] += 1
                except Exception as e:
                    log.warning(f"Error procesando {element.get('type')}/{element.get('id')}: {e}")
                    stats["errors"] += 1

                if i % 500 == 0:
                    log.info(f"  {i}/{len(elements)} procesados — {stats}")
                    if not self.dry_run:
                        await session.flush()

            if not self.dry_run:
                await session.commit()

        log.info(
            f"Sincronización completada: creados={stats['created']} "
            f"actualizados={stats['updated']} sin_cambios={stats['skipped']} "
            f"errores={stats['errors']}"
        )
        return stats

    async def _process(self, session, element: dict) -> str:
        osm_id = f"{element['type']}/{element['id']}"
        tags = element.get("tags", {})

        # Buscar extensión OSM existente
        row = await session.execute(
            select(InmuebleOSMExt).where(InmuebleOSMExt.osm_id == osm_id).limit(1)
        )
        ext = row.scalar_one_or_none()

        if ext:
            version_nueva = element.get("version")
            version_guardada = json.loads(ext.osm_tags or "{}").get("_version", 0)
            if version_nueva and version_nueva > version_guardada:
                if not self.dry_run:
                    ext.osm_tags = self._build_osm_tags(element)
                    await self._update_inmueble(session, ext.inmueble_id, element)
                return "updated"
            return "skipped"
        else:
            if not self.dry_run:
                inmueble = self._build_inmueble(tags)
                session.add(inmueble)
                await session.flush()  # obtiene el id generado

                ext = InmuebleOSMExt(
                    inmueble_id=inmueble.id,
                    osm_type=element["type"],
                    osm_id=osm_id,
                    osm_tags=self._build_osm_tags(element),
                )
                session.add(ext)
            return "created"

    def _build_inmueble(self, tags: dict) -> Inmueble:
        lat, lon = None, None  # se resolverá vía _process donde tenemos el element completo
        tipo_id = self._resolve_tipo(tags)
        return Inmueble(
            nombre=tags.get("name") or "Sin nombre",
            descripcion=_build_description(tags),
            direccion=_build_address(tags),
            tipo_inmueble_id=tipo_id,
        )

    async def _update_inmueble(self, session, inmueble_id: str, element: dict):
        tags = element.get("tags", {})
        row = await session.execute(select(Inmueble).where(Inmueble.id == inmueble_id).limit(1))
        inmueble = row.scalar_one_or_none()
        if not inmueble:
            return
        if name := tags.get("name"):
            inmueble.nombre = name
        new_addr = _build_address(tags)
        if new_addr and len(new_addr) > len(inmueble.direccion or ""):
            inmueble.direccion = new_addr
        lat, lon = _coords(element)
        if lat and lon:
            inmueble.coordenadas = from_shape(Point(lon, lat), srid=4326)

    def _build_inmueble_with_coords(self, element: dict) -> Inmueble:
        """Versión con coords — usada en _process para creación."""
        tags = element.get("tags", {})
        lat, lon = _coords(element)
        return Inmueble(
            nombre=tags.get("name") or "Sin nombre",
            descripcion=_build_description(tags),
            direccion=_build_address(tags),
            tipo_inmueble_id=self._resolve_tipo(tags),
            coordenadas=from_shape(Point(lon, lat), srid=4326) if lat and lon else None,
        )

    def _resolve_tipo(self, tags: dict) -> Optional[str]:
        inferred = _infer_type(tags)
        if inferred:
            nombre = OSM_TIPO_MAP.get(inferred)
            if nombre and nombre in self._tipo_cache:
                return self._tipo_cache[nombre]
        # fallback: Iglesia
        return self._tipo_cache.get("Iglesia")

    def _build_osm_tags(self, element: dict) -> str:
        """Almacena los tags OSM completos más metadatos de control como JSON."""
        tags = element.get("tags", {})
        lat, lon = _coords(element)
        payload = {
            **tags,
            "_version":  element.get("version"),
            "_osm_type": element["type"],
            "_osm_id":   element["id"],
            "_lat":      lat,
            "_lon":      lon,
            "_synced_at": datetime.utcnow().isoformat(),
        }
        return json.dumps(payload, ensure_ascii=False)


# Parche para que _process use _build_inmueble_with_coords
async def _process_patched(self, session, element: dict) -> str:
    osm_id = f"{element['type']}/{element['id']}"

    row = await session.execute(
        select(InmuebleOSMExt).where(InmuebleOSMExt.osm_id == osm_id).limit(1)
    )
    ext = row.scalar_one_or_none()

    if ext:
        version_nueva = element.get("version")
        version_guardada = json.loads(ext.osm_tags or "{}").get("_version", 0)
        if version_nueva and version_nueva > version_guardada:
            if not self.dry_run:
                ext.osm_tags = self._build_osm_tags(element)
                await self._update_inmueble(session, ext.inmueble_id, element)
            return "updated"
        return "skipped"
    else:
        if not self.dry_run:
            inmueble = self._build_inmueble_with_coords(element)
            session.add(inmueble)
            await session.flush()

            ext = InmuebleOSMExt(
                inmueble_id=inmueble.id,
                osm_type=element["type"],
                osm_id=osm_id,
                osm_tags=self._build_osm_tags(element),
            )
            session.add(ext)
        return "created"


# Reemplazar el método _process con la versión que usa coords
OSMSyncAgent._process = _process_patched


# ── Entrypoint ────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Sincronización OSM → SIPI")
    parser.add_argument("--spain",     action="store_true", default=True,
                        help="Sincronizar España completa (por defecto)")
    parser.add_argument("--provincia", type=str,
                        help="Sincronizar solo una provincia (ej: 'Madrid')")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Simular sin escribir en base de datos")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("SINCRONIZACIÓN OSM → SIPI")
    log.info("=" * 60)

    agent = OSMSyncAgent(dry_run=args.dry_run)

    if args.provincia:
        log.info(f"Modo: provincia '{args.provincia}'")
        bbox = await agent.get_provincia_bbox(args.provincia)
        if not bbox:
            log.error("No se pudo obtener el área de la provincia. Abortando.")
            sys.exit(1)
        await agent.sync(bbox=bbox, use_spain=False)
    else:
        log.info("Modo: España completa")
        await agent.sync(use_spain=True)

    log.info("=" * 60)
    log.info("✓ SINCRONIZACIÓN OSM COMPLETADA")
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
