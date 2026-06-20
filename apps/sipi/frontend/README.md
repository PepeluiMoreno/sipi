# apps/sipi/frontend — SPA de SIPI (expedientes)

Aplicación web de gestión de expedientes: Vue 3 (`<script setup>`) + Vite + Pinia +
Apollo (GraphQL) + Leaflet (mapa).

Consume la API GraphQL de `apps/sipi/api`. El endpoint se configura por variable de
entorno (`VITE_API_URL`, p. ej. `http://localhost:8040/graphql`) — no hardcodeado.

## Desarrollo

```bash
pnpm install
echo "VITE_API_URL=http://localhost:8040/graphql" > .env
pnpm dev            # http://localhost:5173
```

## Módulos principales

Inmuebles, entidades religiosas, **bandeja de validación de hallazgos**
(`expedientes` en estado `propuesto`), notificaciones, y mapa. Las pantallas se
alinean al contrato GraphQL autogenerado por la API (estilo `xs(limit,offset,filters)`).

> Histórico de cambios y notas de sesión previas: ver historial de git.
