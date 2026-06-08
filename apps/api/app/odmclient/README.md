# odmclient

SIPI como **cliente** de OpenDataManager (ODM). No publica recursos: declara y
mantiene el *desired-state* de recursos (de sus publishers reales) que consume.

## Estructura
- `manifests/*.json` — un manifiesto declarativo por recurso ODM (publisher + resource).
- `apply_manifests.py` — motor único e idempotente que aplica los manifiestos vía
  GraphQL (upsert: publisher por acrónimo, resource por nombre). Mapea al
  `CreateResourceInput` real de ODM.

## Uso
```bash
# dry-run: SOLO lee ODM y muestra el plan (no escribe)
python -m app.odmclient.apply_manifests --base-url https://odmgr.pepelui.es --token "$ODM_TOKEN"
# aplicar (escribe en ODM) — requiere autorización previa:
python -m app.odmclient.apply_manifests --base-url ... --token ... --apply
```

## Gobernanza
- Coleccionar/editar manifiestos = lado SIPI, libre.
- `--apply` escribe en ODM -> **gateado**: el diff del manifiesto es el artefacto
  de comprensión; se aprueba y solo entonces se aplica.

## Recursos rescatados (de seed_resources.py de ODM)
- `notarias_cgn.json` — Notarías, Guía Notarial (CGN), fetcher REST Loop (pivota provincias).
- `registros_corpme.json` — Registros de la Propiedad (CORPME), File Download xlsx.
  AVISO: URL caducada (404 en auditoría ODM); registradores.org renombró el documento.
