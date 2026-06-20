# -*- coding: utf-8 -*-
"""Cliente del consumidor ODM.

Dos vías de consumo, ambas contra el contrato real de opendatamanager:

1. BACKFILL (poblado masivo, sin webhook): resuelve recurso→último dataset por
   GraphQL admin (`/graphql`) y descarga en streaming el JSONL
   (`/api/datasets/{id}/data.jsonl`), entregando registros normalizados.

2. WEBHOOK (incremental, push): verificación de firma HMAC-SHA256 de la
   cabecera `X-ODM-Signature` y extracción de `download_urls.data` del payload.

No reimplementa extracción de fuentes: eso es trabajo de ODM.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import urllib.request
from typing import Iterator, Optional

from . import config


class ODMError(RuntimeError):
    pass


class ODMClient:
    def __init__(self, base_url: str = None, app_token: str = None, timeout: int = 120):
        self.base_url = (base_url or config.ODM_BASE_URL).rstrip("/")
        self.app_token = app_token or config.ODM_APP_TOKEN
        self.timeout = timeout
        if not self.base_url:
            raise ODMError("ODM_BASE_URL no configurada.")

    # -- HTTP helpers ----------------------------------------------------------
    def _headers(self) -> dict:
        h = {"User-Agent": "sipi-etl/odm-consumer"}
        if self.app_token:
            h["Authorization"] = f"Bearer {self.app_token}"
        return h

    def _post_json(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode("utf-8"),
            headers={**self._headers(), "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    # -- Preparación del ETL: suscripción declarativa + readiness (M2M) --------
    def request_subscriptions(self, collection_slugs) -> list:
        """Declara (idempotente) las suscripciones a colecciones que SIPI necesita,
        por slug. Requiere ODM_APP_TOKEN (auth Bearer de la aplicación)."""
        query = ("mutation($slugs:[String!]!){ requestSubscriptions(collectionSlugs:$slugs)"
                 "{ id collectionId } }")
        data = self._post_json("/graphql", {"query": query,
                                            "variables": {"slugs": list(collection_slugs)}})
        if data.get("errors"):
            raise ODMError(f"requestSubscriptions error: {data['errors']}")
        return (data.get("data") or {}).get("requestSubscriptions") or []

    def my_subscriptions(self) -> list:
        """Readiness de las suscripciones de esta aplicación (¿satisfechas?)."""
        query = ("query{ mySubscriptions{ subscriptionId targetKind targetName targetSlug "
                 "active satisfied currentVersion latestDatasetId dataUrl memberCount "
                 "satisfiedMemberCount } }")
        data = self._post_json("/graphql", {"query": query})
        if data.get("errors"):
            raise ODMError(f"mySubscriptions error: {data['errors']}")
        return (data.get("data") or {}).get("mySubscriptions") or []

    def bootstrap_suscripciones(self, slugs=None) -> list:
        """Preparación del ETL: pide las suscripciones necesarias (idempotente) y
        devuelve el readiness, marcando en el log las que NO están satisfechas.

        La "preparación" del consumidor es por tanto una solicitud de suscripción a
        ODM, no configuración manual. Requiere ODM_APP_TOKEN."""
        import logging
        log = logging.getLogger("sipi.etl.odm")
        slugs = list(slugs if slugs is not None else config.SLUGS_NECESARIOS)
        if not self.app_token:
            log.warning("bootstrap_suscripciones: sin ODM_APP_TOKEN; se omite la "
                        "suscripción declarativa (configura el token Bearer M2M).")
            return []
        self.request_subscriptions(slugs)
        readiness = self.my_subscriptions()
        por_slug = {r.get("targetSlug"): r for r in readiness if r.get("targetSlug")}
        for slug in slugs:
            r = por_slug.get(slug)
            if r is None:
                log.warning("Colección '%s' no existe en ODM (créala y añádele recursos).", slug)
            elif not r.get("satisfied"):
                log.warning("Colección '%s' suscrita pero SIN datos aún (%s/%s miembros con dataset).",
                            slug, r.get("satisfiedMemberCount"), r.get("memberCount"))
            else:
                log.info("Colección '%s' lista (%s/%s miembros con dataset).",
                         slug, r.get("satisfiedMemberCount"), r.get("memberCount"))
        return readiness

    # -- Backfill: recurso -> último dataset -> JSONL --------------------------
    def latest_dataset_id(self, resource_name: str) -> str:
        """Devuelve el id del último dataset publicado de un recurso (admin GraphQL).

        La forma exacta de la query admin depende del schema de ODM; este es el
        patrón estándar expuesto por opendatamanager. Si el nombre del campo
        difiere, ajustar aquí (único punto de acoplamiento al schema admin).
        """
        query = """
        query($name: String!) {
          resources(name: $name) {
            id
            name
            latestDataset { id versionString recordCount }
          }
        }
        """
        data = self._post_json("/graphql", {"query": query, "variables": {"name": resource_name}})
        if data.get("errors"):
            raise ODMError(f"GraphQL admin error para '{resource_name}': {data['errors']}")
        resources = (data.get("data") or {}).get("resources") or []
        if not resources or not resources[0].get("latestDataset"):
            raise ODMError(f"Sin dataset publicado para recurso '{resource_name}'.")
        return resources[0]["latestDataset"]["id"]

    def iter_jsonl(self, dataset_id: str) -> Iterator[dict]:
        """Descarga en streaming el JSONL de un dataset y entrega dict por línea."""
        url = f"{self.base_url}/api/datasets/{dataset_id}/data.jsonl"
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            for raw in r:
                line = raw.decode("utf-8").strip()
                if line:
                    yield json.loads(line)

    def iter_resource(self, resource_name: str) -> Iterator[dict]:
        """Atajo: registros normalizados del último dataset de un recurso."""
        yield from self.iter_jsonl(self.latest_dataset_id(resource_name))

    # -- Webhook: verificación de firma ---------------------------------------
    @staticmethod
    def verify_signature(raw_body: bytes, signature: str, secret: str = None) -> bool:
        """Verifica X-ODM-Signature (HMAC-SHA256). ODM firma sobre el payload
        serializado con sort_keys=True; reproducimos esa forma."""
        secret = secret if secret is not None else config.ODM_WEBHOOK_SECRET
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            return False
        expected = hmac.new(
            secret.encode("utf-8"),
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, (signature or "").strip())

    def iter_from_webhook_payload(self, payload: dict) -> Iterator[dict]:
        """Dado el payload de webhook (consumption_mode webhook/both), descarga
        el JSONL referido en download_urls.data."""
        data_path = (payload.get("download_urls") or {}).get("data")
        if not data_path:
            # consumption_mode == graphql: no hay descarga masiva en el payload
            ds = (payload.get("dataset") or {}).get("id")
            if not ds:
                raise ODMError("Payload sin download_urls ni dataset.id.")
            yield from self.iter_jsonl(ds)
            return
        req = urllib.request.Request(self.base_url + data_path, headers=self._headers())
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            for raw in r:
                line = raw.decode("utf-8").strip()
                if line:
                    yield json.loads(line)
