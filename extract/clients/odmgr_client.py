"""
extract/clients/odmgr_client.py — Cliente para la API GraphQL de datos de OpenDataManager

Consume el endpoint /graphql/data de ODMGR con paginación automática (limit/offset).

Nombres de query GraphQL:
    Los nombres se derivan del nombre del recurso en ODMGR usando camelCase:
    "España - Comunidades Autónomas (INE)" → "espanaComunidadesAutonomasIne"
    "España - Provincias (INE)"            → "espanaProvinciasIne"
    "España - Municipios (INE)"            → "espanaMunicipiosIne"
    "Geonames - Entidades de Población (España)" → "geonamesEntidadesDePoblacionEspana"

Uso:
    client = ODMGRClient("http://172.18.0.3:8000")
    for record in client.fetch_all("espanaProvinciasIne", ["Codigo", "Nombre", "FK_JerarquiaPadres"]):
        print(record)
"""

import json
import os
import re
import urllib.error
import urllib.request
from typing import Generator, Iterator

# URL por defecto: red traefik_public donde vive ODMGR
ODMGR_URL_DEFAULT = os.environ.get("ODMGR_URL", "http://172.18.0.3:8000")

# Mapa de sustitución de caracteres para normalizar nombres a camelCase
_ACCENT_MAP = str.maketrans(
    "áéíóúÁÉÍÓÚñÑüÜ",
    "aeiouAEIOUnNuU",
)


def resource_name_to_query(resource_name: str) -> str:
    """
    Convierte el nombre de un recurso ODMGR en el nombre de la query GraphQL (camelCase).

    Ejemplos:
        "España - Comunidades Autónomas (INE)" → "espanaComunidadesAutonomasIne"
        "España - Provincias (INE)"            → "espanaProvinciasIne"
    """
    name = resource_name.translate(_ACCENT_MAP)
    words = [w for w in re.split(r"[^a-zA-Z0-9]+", name) if w]
    if not words:
        return ""
    pascal = "".join(w.capitalize() for w in words)
    return pascal[0].lower() + pascal[1:]


class ODMGRClient:
    """
    Cliente ligero para la API GraphQL de datos de ODMGR.

    Solo necesita la URL base de ODMGR. Las queries son dinámicas — se construyen
    a partir de los campos solicitados y el nombre de la query.
    """

    def __init__(self, base_url: str = ODMGR_URL_DEFAULT):
        self.data_url = f"{base_url.rstrip('/')}/graphql/data"

    # ── API pública ────────────────────────────────────────────────────────────

    def fetch_all(
        self,
        query_name: str,
        fields: list[str],
        page_size: int = 500,
        filters: dict | None = None,
    ) -> Iterator[dict]:
        """
        Itera sobre todos los registros de un dataset ODMGR.

        Args:
            query_name:  Nombre camelCase de la query GraphQL (e.g. "espanaProvinciasIne")
            fields:      Lista de campos a recuperar (e.g. ["Codigo", "Nombre"])
            page_size:   Registros por página (máx 1000 en ODMGR)
            filters:     Filtros adicionales como dict {campo: valor}

        Yields:
            Dicts con los campos solicitados para cada registro.
        """
        fields_str = " ".join(fields)
        filter_args = ""
        if filters:
            filter_parts = [f'{k}: "{v}"' for k, v in filters.items()]
            filter_args = ", ".join(filter_parts)

        offset = 0
        while True:
            args = f"limit: {page_size}, offset: {offset}"
            if filter_args:
                args += f", {filter_args}"

            query = f"""
            {{
                {query_name}({args}) {{
                    total
                    limit
                    offset
                    items {{
                        {fields_str}
                    }}
                }}
            }}
            """
            result = self._gql(query)
            data = result.get("data", {}).get(query_name, {})
            items = data.get("items", [])

            if not items:
                break

            yield from items

            offset += len(items)
            if offset >= data.get("total", 0):
                break

    def count(self, query_name: str) -> int:
        """Devuelve el número total de registros de un dataset."""
        query = f"{{ {query_name}(limit: 1) {{ total }} }}"
        result = self._gql(query)
        return result.get("data", {}).get(query_name, {}).get("total", 0)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _gql(self, query: str, variables: dict | None = None) -> dict:
        payload = json.dumps({"query": query, "variables": variables or {}}).encode()
        req = urllib.request.Request(
            self.data_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                result = json.loads(body)
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"No se puede conectar a ODMGR en {self.data_url}: {e}\n"
                "Verifica que ODMGR está corriendo y que ODMGR_URL es correcta."
            ) from e

        if "errors" in result:
            msgs = [e.get("message", str(e)) for e in result["errors"]]
            raise ValueError(f"GraphQL error en '{query_name_from_query(query)}': {'; '.join(msgs)}")

        return result


def query_name_from_query(query: str) -> str:
    """Extrae el nombre de la query de un string GraphQL (para mensajes de error)."""
    m = re.search(r"\{\s*(\w+)\s*\(", query)
    return m.group(1) if m else "?"
