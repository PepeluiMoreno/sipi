# Deploy a staging (sipi.pepelui.es)

Fase 1 del enganche con ODM: **BD + receptor ETL**. Se despliega con el workflow
**Deploy SIPI** (manual), que construye la imagen del ETL, la publica en GHCR y
hace SSH-deploy con [`docker-compose.staging.yml`](../docker-compose.staging.yml).

**Host único**: `sipi.pepelui.es`. Traefik enruta **por path**: el
receptor del webhook se expone en `/odm` de ese host; la BD y (en Fase 2) la API
quedan **internas**, sin salir de la red de contenedores.

> El frontend y la API llegarán en Fase 2: requieren empaquetar `sipi-core` para
> prod (hoy la API lo consume por volumen en dev) y, en el frontend, hablar con la
> API por la red interna. El frontend servirá `/` en el mismo host.

## 1. Secrets del repo (Settings → Secrets and variables → Actions)

| Secret | Para qué |
|---|---|
| `DEPLOY_HOST` | host SSH del servidor de staging |
| `DEPLOY_USER` | usuario SSH |
| `DEPLOY_KEY` | clave privada SSH (el público en el servidor) |
| `SIPI_ENV_PRODUCTION` | contenido de `.env.production` (ver [`.env.staging.example`](../.env.staging.example)) |
| `DEPLOY_PATH` *(opcional)* | ruta del repo en el servidor (def. `/opt/docker/apps/sipi`) |

## 2. Requisitos en el servidor (ya listos)

- Repo clonado en `DEPLOY_PATH`, en la rama `master`.
- **Traefik** corriendo en la red externa `traefik_public` con un **certresolver**
  de Let's Encrypt (su nombre va en `TRAEFIK_CERTRESOLVER`, def. `letsencrypt`).
- **DNS**: `sipi.pepelui.es` → IP del servidor.

## 3. Lanzar

GitHub → **Actions → Deploy SIPI → Run workflow**. El job:

1. construye y publica `ghcr.io/pepeluimoreno/sipi-etl:latest`,
2. por SSH: `git pull` de master, escribe `.env.production` desde el secret,
3. `docker compose -f docker-compose.staging.yml`:
   - `pull etl-webhook`
   - `--profile migrate run --rm etl-migrate` (alembic upgrade head, idempotente)
   - `up -d --build --remove-orphans` (levanta `db` + `etl-webhook`).

## 4. Comprobar

- `https://sipi.pepelui.es/odm/webhook` responde (un GET dará 405 —
  el endpoint es POST — pero confirma que Traefik enruta el path al contenedor).
- Health interno del receptor: `docker compose -f docker-compose.staging.yml exec
  etl-webhook python -c "import urllib.request;print(urllib.request.urlopen('http://localhost:8000/health').read())"`
  (no se expone por Traefik: solo `/odm` sale fuera).
- Logs del receptor: al arrancar ejecuta `bootstrap_suscripciones` (si
  `ODM_APP_TOKEN` está puesto) → registra el *readiness* por colección.

## 5. Conectar con ODM

En ODM, el **Subscriber** de SIPI:
- `webhook_url = https://sipi.pepelui.es/odm/webhook`
- `webhook_secret` = el mismo valor que `ODM_WEBHOOK_SECRET` del `.env.production`.

Detalle del contrato y el enrutado por slug en
[`services/discovery/etl/docs/CONSUMO_ODM.md`](../services/discovery/etl/docs/CONSUMO_ODM.md).
