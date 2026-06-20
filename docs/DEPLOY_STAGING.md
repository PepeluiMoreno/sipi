# Deploy a staging (sipi-etl.staging.europalaica.org)

Fase 1 del enganche con ODM: **BD + receptor ETL**. Se despliega con el workflow
**Deploy SIPI** (manual), que construye la imagen del ETL, la publica en GHCR y
hace SSH-deploy con [`docker-compose.staging.yml`](../docker-compose.staging.yml).

> La API y el frontend llegarán en Fase 2: requieren empaquetar `sipi-core` para
> prod (hoy la API lo consume por volumen en dev) y añadir el proxy `/graphql` al
> nginx del frontend.

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
- **DNS**: `sipi-etl.staging.europalaica.org` → IP del servidor.

## 3. Lanzar

GitHub → **Actions → Deploy SIPI → Run workflow**. El job:

1. construye y publica `ghcr.io/pepeluimoreno/sipi-etl:latest`,
2. por SSH: `git pull` de master, escribe `.env.production` desde el secret,
3. `docker compose -f docker-compose.staging.yml`:
   - `pull etl-webhook`
   - `--profile migrate run --rm etl-migrate` (alembic upgrade head, idempotente)
   - `up -d --build --remove-orphans` (levanta `db` + `etl-webhook`).

## 4. Comprobar

- `https://sipi-etl.staging.europalaica.org/health` → `{"status":"healthy"}`.
- Logs del receptor: al arrancar ejecuta `bootstrap_suscripciones` (si
  `ODM_APP_TOKEN` está puesto) → registra el *readiness* por colección.

## 5. Conectar con ODM

En ODM, el **Subscriber** de SIPI:
- `webhook_url = https://sipi-etl.staging.europalaica.org/odm/webhook`
- `webhook_secret` = el mismo valor que `ODM_WEBHOOK_SECRET` del `.env.production`.

Detalle del contrato y el enrutado por slug en
[`services/discovery/etl/docs/CONSUMO_ODM.md`](../services/discovery/etl/docs/CONSUMO_ODM.md).
