# -*- coding: utf-8 -*-
"""Configuración del consumidor ODM y enrutado recurso→destino.

SIPI deja de extraer: consume los *recursos* (piezas) que produce
OpenDataManager (ODM) y los resuelve sobre los modelos de `sipi-core`. El
ensamblaje (fusión CEE×OSM, scoring, hallazgos) sigue siendo del consumidor.

Contrato ODM verificado contra el repo opendatamanager:
  - Notificación push: webhook firmado HMAC-SHA256 en cabecera `X-ODM-Signature`
    (firma = hmac(secret, json.dumps(payload, sort_keys=True))).
  - Payload completo: {event, dataset:{id,resource_name,version,...},
    download_urls:{data:"/api/datasets/{id}/data.jsonl", schema, models, metadata}}.
  - Backfill: GraphQL admin en `/graphql` para resolver recurso→último dataset,
    y descarga masiva del JSONL en `/api/datasets/{id}/data.jsonl`.
  - Consumo GraphQL fino: POST `/graphql/data` (no usado aquí; preferimos JSONL
    para poblado masivo).
"""
import os

# --- Conexión a ODM (se rellena en tiempo de ejecución) ------------------------
ODM_BASE_URL = os.environ.get("ODM_BASE_URL", "").rstrip("/")
ODM_WEBHOOK_SECRET = os.environ.get("ODM_WEBHOOK_SECRET", "")
# Token/clave de aplicación si ODM exige auth M2M para /graphql y /api/datasets:
ODM_APP_TOKEN = os.environ.get("ODM_APP_TOKEN", "")

# Tamaño de lote para commits durante el poblado
BATCH_SIZE = int(os.environ.get("SIPI_ETL_BATCH", "500"))


# --- Enrutado: nombre de recurso ODM -> (dominio, fuente) ----------------------
# El "dominio" elige el resolver; la "fuente" se guarda como procedencia.
# Los nombres deben coincidir EXACTAMENTE con `resource.name` en ODM
# (ver manifests/*.json del repo opendatamanager).
RESOURCE_MAP = {
    # --- Agentes: instituciones religiosas ---
    "Diócesis de España (Conferencia Episcopal)":      ("diocesis", "CEE"),
    "Registro de Entidades Religiosas (RER)":          ("entidad_religiosa", "RER"),
    "Parroquias de España (directorio CEE)":           ("entidad_religiosa", "CEE_PARROQUIA"),
    "Comunidades religiosas (CONFER, mapa de congregaciones)": ("entidad_religiosa", "CONFER"),
    "Institutos religiosos (CONFER, directorio)":      ("entidad_religiosa", "CONFER"),

    # --- Agentes: administraciones públicas (DIR3 / BDNS órganos) ---
    "BDNS - Órganos Convocantes (Estatal)":            ("administracion", "DIR3"),
    "BDNS - Órganos Convocantes (Autonómica)":         ("administracion", "DIR3"),
    "BDNS - Órganos Convocantes (Local)":              ("administracion", "DIR3"),
    "BDNS - Órganos Convocantes (Otros)":              ("administracion", "DIR3"),
    "BDNS - Puente DIR3 ↔ Órganos":                    ("administracion", "DIR3_PUENTE"),

    # --- Agentes: fe pública (manifests ODM NUEVOS, ver manifests_pendientes/) ---
    "Notarías de España (CGN)":                        ("notaria", "CGN"),
    "Registros de la Propiedad de España (CORPME)":    ("registro_propiedad", "CORPME"),

    # --- Inmuebles ---
    "Lugares de culto en España (OSM)":                ("inmueble", "OSM"),
    "Patrimonio Inmueble de Andalucía (IAPH)":         ("inmueble", "IAPH"),
    # CEE inmatriculaciones (listado de 34.961 fincas): falta manifest ODM
    # estable; cuando exista, mapear aquí -> ("inmueble", "CEE_INMATRICULACION").
}


# --- Enrutado por COLECCIÓN (preferente), por SLUG ---------------------------
# SIPI se suscribe en ODM a COLECCIONES (no recurso a recurso). El enrutado va por
# el `slug` de colección — la CLAVE ESTABLE de ODM (no el nombre de display, que es
# editable y frágil; ni el UUID, que cambia entre entornos). El webhook trae
# `collection_slugs`; mapeamos slug → (dominio, fuente). Cuando ODM añade un recurso
# nuevo a una colección suscrita, SIPI lo procesa SIN tocar este fichero.
#
# Esta tabla es a la vez la DECLARACIÓN DE NECESIDADES de SIPI (los slugs que pide
# en `requestSubscriptions`, ver client.bootstrap_suscripciones) y el MAPA DE
# ENRUTADO. Las colecciones en ODM son neutrales/compartibles (sin prefijo de app);
# `RESOURCE_MAP` queda como override fino por recurso (gana sobre la colección).
# fuente=None → se deriva por recurso (fallback por publisher/nombre).
COLLECTION_MAP = {
    "administraciones-dir3":       ("administracion", "DIR3"),
    "diocesis":                    ("diocesis", "CEE"),
    "entidades-religiosas":        ("entidad_religiosa", None),   # fuente por recurso
    "notarias":                    ("notaria", "CGN"),
    "registros-de-la-propiedad":   ("registro_propiedad", "CORPME"),
    "inmuebles":                   ("inmueble", None),            # fuente por recurso (OSM/IAPH/CEE)
}

# Slugs que SIPI necesita: lo que `bootstrap_suscripciones` pide a ODM.
SLUGS_NECESARIOS = tuple(COLLECTION_MAP.keys())


def _slugify(name: str) -> str:
    """Reproduce el slug de ODM (minúsculas, no-alfanuméricos → '-'). Permite
    derivar el slug desde un nombre cuando el payload no trae `collection_slugs`
    (compatibilidad con emisores antiguos)."""
    import re
    base = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return (base or "coleccion")[:120]


def _fuente_fallback(resource_name: str, publisher: str | None) -> str:
    """Procedencia derivada cuando la colección no fija `fuente`: usa el publisher
    (acrónimo/nombre) o, en su defecto, un slug del nombre del recurso."""
    base = (publisher or resource_name or "ODM").strip()
    return base.upper().replace(" ", "_")[:40] or "ODM"


def resolver_destino(resource_name: str, collection_slugs=None,
                     publisher: str | None = None, collections=None):
    """Resuelve (dominio, fuente) para un recurso ODM. Devuelve None si no aplica.

    Prioridad: 1) RESOURCE_MAP[resource_name] (override fino, fuente exacta);
               2) primer `slug` del recurso presente en COLLECTION_MAP;
               3) compat: slugify de los nombres de `collections` (emisores viejos).
    """
    if resource_name in RESOURCE_MAP:
        return RESOURCE_MAP[resource_name]
    for slug in (collection_slugs or []):
        if slug in COLLECTION_MAP:
            dominio, fuente = COLLECTION_MAP[slug]
            return (dominio, fuente or _fuente_fallback(resource_name, publisher))
    for col in (collections or []):
        slug = _slugify(col)
        if slug in COLLECTION_MAP:
            dominio, fuente = COLLECTION_MAP[slug]
            return (dominio, fuente or _fuente_fallback(resource_name, publisher))
    return None


def require_connection():
    """Falla pronto y claro si no hay datos de conexión a ODM."""
    missing = [k for k, v in (("ODM_BASE_URL", ODM_BASE_URL),) if not v]
    if missing:
        raise RuntimeError(
            "Falta configuración de ODM: " + ", ".join(missing) +
            ". Exporta ODM_BASE_URL (y ODM_APP_TOKEN si ODM exige auth)."
        )
