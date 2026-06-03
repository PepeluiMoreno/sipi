# -*- coding: utf-8 -*-
"""Cliente del lado SIPI para OpenDataManager (ODM).

Habla con las dos APIs de ODM (sin dependencias externas, urllib de stdlib):

- **API de datos** (`POST {base}/graphql/data`, graphql-core puro): meta-query
  `{ datasets { queryName fields } }` para descubrir datasets y luego consultar
  cada uno por su `queryName`.
- **API admin** (`POST {base}/graphql`, Strawberry): `resources`,
  `executeResource(id)` (refresco a demanda), `createApplication`,
  `datasetSubscriptions`, `setApplicationWebhook`.

Las rutas son configurables por entorno (ODM_BASE_URL, ODM_DATA_PATH,
ODM_ADMIN_PATH) porque el montaje exacto del endpoint admin no está fijado aquí.
No ejecuta nada contra ODM en import; requiere una instancia viva para funcionar.
"""
import json
import os
import urllib.request
import urllib.error

__all__ = ["ODMClient", "ODMError"]


class ODMError(RuntimeError):
    pass


class ODMClient:
    def __init__(self, base_url=None, data_path=None, admin_path=None, token=None, timeout=60):
        self.base = (base_url or os.getenv("ODM_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.data_path = data_path or os.getenv("ODM_DATA_PATH", "/graphql/data")
        self.admin_path = admin_path or os.getenv("ODM_ADMIN_PATH", "/graphql")
        self.token = token or os.getenv("ODM_TOKEN")
        self.timeout = timeout

    # ── transporte ────────────────────────────────────────────────────────
    def _post(self, path, query, variables=None):
        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.base + path, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = json.loads(r.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ODMError(f"ODM no accesible en {self.base}{path}: {e}") from e
        if body.get("errors"):
            raise ODMError(f"GraphQL error: {body['errors']}")
        return body.get("data", {})

    def _data(self, query, variables=None):
        return self._post(self.data_path, query, variables)

    def _admin(self, query, variables=None):
        return self._post(self.admin_path, query, variables)

    # ── API de datos ──────────────────────────────────────────────────────
    def list_datasets(self):
        """Lista los datasets expuestos: [{'queryName':..., 'fields':[...]}]."""
        data = self._data("{ datasets { queryName fields } }")
        return data.get("datasets", [])

    def fetch_dataset(self, query_name, fields, limit=None):
        """Trae las filas de un dataset por su queryName y la lista de campos.

        El schema de datos es dinámico; los argumentos de paginación/limite
        dependen del dataset (a confirmar contra la instancia). Si `limit` se
        indica, se intenta pasar como argumento `limit`.
        """
        sel = " ".join(fields)
        arg = f"(limit: {int(limit)})" if limit else ""
        data = self._data(f"{{ {query_name}{arg} {{ {sel} }} }}")
        return data.get(query_name, [])

    # ── API admin ──────────────────────────────────────────────────────────
    def list_resources(self, active_only=True):
        q = """query($a: Boolean){ resources(activeOnly: $a){ id name project schedule active } }"""
        return self._admin(q, {"a": active_only}).get("resources", [])

    def execute_resource(self, resource_id, params=None):
        """Dispara un refresco a demanda de un resource."""
        q = """mutation($id: String!, $p: JSON){ executeResource(id: $id, params: $p){ success message } }"""
        return self._admin(q, {"id": resource_id, "p": params}).get("executeResource")

    def create_application(self, name, subscribed_projects):
        q = """mutation($i: CreateApplicationInput!){ createApplication(input: $i){ id name subscribedProjects } }"""
        return self._admin(q, {"i": {"name": name, "subscribedProjects": subscribed_projects}}).get("createApplication")

    def dataset_subscriptions(self, application_id=None):
        q = """query($a: String){ datasetSubscriptions(applicationId: $a){ id resourceId currentVersion notifiedAt } }"""
        return self._admin(q, {"a": application_id}).get("datasetSubscriptions", [])

    def set_webhook(self, application_id, webhook_url, webhook_secret):
        q = """mutation($id:String!,$u:String!,$s:String!){ setApplicationWebhook(id:$id, webhookUrl:$u, webhookSecret:$s){ id } }"""
        return self._admin(q, {"id": application_id, "u": webhook_url, "s": webhook_secret}).get("setApplicationWebhook")
