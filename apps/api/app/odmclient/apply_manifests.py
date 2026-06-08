#!/usr/bin/env python3
"""
odmclient/apply_manifests.py — motor ÚNICO y genérico que aplica los manifiestos
de recursos ODM (manifests/*.json) sobre una instancia de OpenDataManager.

Patrón desired-state (estilo `kubectl apply`): lee los manifiestos y hace UPSERT
idempotente contra ODM vía GraphQL —
  · publisher: createPublisher / updatePublisher (match por acrónimo)
  · resource : createResource  / updateResource  (match por name)
Fiel al CreateResourceInput real de ODM (fetcherId, publisherId, targetTable,
schedule, params=[{key,value,isExternal}]).

SEGURIDAD / GOBERNANZA:
  · Por defecto DRY-RUN: solo CONSULTA ODM (lecturas) y muestra el plan. No escribe.
  · --apply ejecuta las mutations. ESO escribe en ODM → requiere autorización
    explícita previa (regla de gobernanza de ODM). El dry-run es el artefacto de
    comprensión: enséñalo, apruébalo, y solo entonces --apply.

Sin dependencias externas (stdlib urllib), igual que el ODMClient del proyecto.

Uso:
  # dry-run (no escribe): muestra qué crearía/actualizaría
  python -m odmclient.apply_manifests --base-url https://odmgr.pepelui.es --token "$ODM_TOKEN"
  # aplicar de verdad (tras autorización):
  python -m odmclient.apply_manifests --base-url ... --token ... --apply
"""
from __future__ import annotations
import argparse, glob, json, os, sys, urllib.request, urllib.error
from typing import Any, Dict, List, Optional

MANIFESTS_DIR = os.path.join(os.path.dirname(__file__), "manifests")

# ── GraphQL (stdlib) ──────────────────────────────────────────────────────────
class Gql:
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 30):
        self.url = base_url.rstrip("/") + "/graphql"
        self.token = token
        self.timeout = timeout

    def __call__(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = json.dumps({"query": query, "variables": variables or {}}).encode()
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode())
        except urllib.error.URLError as e:
            raise RuntimeError(f"ODM no accesible: {e}")
        if data.get("errors"):
            raise RuntimeError("; ".join(str(e) for e in data["errors"]))
        return data["data"]

# ── Queries / mutations (mismas shapes que seed_resources.py de ODM) ───────────
Q_FETCHERS   = "{ fetchers { id name } }"
Q_PUBLISHERS = "{ publishers { id acronimo nombre } }"
Q_RESOURCES  = "{ resources { id name } }"
M_CREATE_PUB = "mutation($input: CreatePublisherInput!){ createPublisher(input:$input){ id acronimo } }"
M_UPDATE_PUB = "mutation($id:String!,$input: UpdatePublisherInput!){ updatePublisher(id:$id,input:$input){ id } }"
M_CREATE_RES = "mutation($input: CreateResourceInput!){ createResource(input:$input){ id name } }"
M_UPDATE_RES = "mutation($id:String!,$input: UpdateResourceInput!){ updateResource(id:$id,input:$input){ id } }"

# ── Mapeo manifiesto → input ODM ──────────────────────────────────────────────
def publisher_input(p: Dict[str, Any]) -> Dict[str, Any]:
    inp = {"nombre": p["nombre"], "nivel": p["nivel"], "pais": p.get("pais", "España")}
    if p.get("acronimo"):           inp["acronimo"] = p["acronimo"]
    if p.get("comunidad_autonoma"): inp["comunidadAutonoma"] = p["comunidad_autonoma"]
    if p.get("provincia"):          inp["provincia"] = p["provincia"]
    if p.get("municipio"):          inp["municipio"] = p["municipio"]
    if p.get("portal_url"):         inp["portalUrl"] = p["portal_url"]
    return inp

def params_list(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for k, v in raw.items():
        if isinstance(v, dict) and "value" in v:
            out.append({"key": k, "value": str(v["value"]), "isExternal": bool(v.get("is_external", False))})
        else:
            out.append({"key": k, "value": str(v), "isExternal": False})
    return out

# ── Carga de manifiestos ──────────────────────────────────────────────────────
def load_manifests(d: str) -> List[Dict[str, Any]]:
    mans = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        m = json.load(open(f, encoding="utf-8"))
        m["_file"] = os.path.basename(f)
        mans.append(m)
    return mans

# ── Plan + apply ──────────────────────────────────────────────────────────────
def run(base_url: str, token: Optional[str], manifests_dir: str, do_apply: bool) -> int:
    mans = load_manifests(manifests_dir)
    if not mans:
        print(f"No hay manifiestos en {manifests_dir}"); return 1
    gql = Gql(base_url, token)

    fetchers = {f["name"]: f["id"] for f in gql(Q_FETCHERS)["fetchers"]}
    pubs     = {(p.get("acronimo") or ""): p for p in gql(Q_PUBLISHERS)["publishers"]}
    res      = {r["name"]: r for r in gql(Q_RESOURCES)["resources"]}

    print(f"== {'APLICANDO' if do_apply else 'DRY-RUN (no escribe)'} · {base_url} · {len(mans)} manifiestos ==\n")
    problemas = 0

    for m in mans:
        p, r = m.get("publisher"), m["resource"]
        acr = (p or {}).get("acronimo", "")
        fname = r["fetcher"]
        fid = fetchers.get(fname)

        # publisher
        if p:
            verb = "update" if acr in pubs else "create"
            print(f"[{m['_file']}] publisher {acr or p['nombre']}: {verb}")
            if do_apply:
                if verb == "create":
                    pubs[acr] = gql(M_CREATE_PUB, {"input": publisher_input(p)})["createPublisher"]
                else:
                    gql(M_UPDATE_PUB, {"id": pubs[acr]["id"], "input": publisher_input(p)})

        # resource
        if fid is None:
            print(f"[{m['_file']}] ⚠ fetcher '{fname}' no existe en ODM — recurso OMITIDO ('{r['name']}')")
            problemas += 1
            continue
        pid = (pubs.get(acr) or {}).get("id")
        verb = "update" if r["name"] in res else "create"
        print(f"[{m['_file']}] resource '{r['name']}': {verb}  (fetcher={fname}, target={r.get('target_table')})")

        if do_apply:
            inp = {"fetcherId": fid, "active": r.get("active", True), "params": params_list(r.get("params", {}))}
            if r.get("target_table") is not None: inp["targetTable"] = r["target_table"]
            if r.get("schedule"):                 inp["schedule"] = r["schedule"]
            if r.get("description"):              inp["description"] = r["description"]
            if pid:                               inp["publisherId"] = pid
            if verb == "create":
                inp["name"] = r["name"]
                gql(M_CREATE_RES, {"input": inp})
            else:
                gql(M_UPDATE_RES, {"id": res[r["name"]]["id"], "input": inp})

    print(f"\n{'Aplicado' if do_apply else 'Plan'} OK. Problemas: {problemas}")
    if not do_apply:
        print("Esto NO ha escrito nada. Para ejecutar (requiere autorización): añade --apply")
    return 0 if problemas == 0 else 2

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("ODM_BASE_URL", "https://odmgr.pepelui.es"))
    ap.add_argument("--token", default=os.environ.get("ODM_TOKEN", ""))
    ap.add_argument("--manifests", default=MANIFESTS_DIR)
    ap.add_argument("--apply", action="store_true", help="Ejecuta las mutations (escribe en ODM). Requiere autorización previa.")
    a = ap.parse_args()
    return run(a.base_url, a.token or None, a.manifests, a.apply)

if __name__ == "__main__":
    raise SystemExit(main())
