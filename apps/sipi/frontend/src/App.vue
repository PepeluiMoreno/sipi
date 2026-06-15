<template>
  <router-view />
  <ConfirmHost />
</template>

<script setup>
import { onMounted } from 'vue'
import ConfirmHost from './modules/core/components/ConfirmHost.vue'
import { useLazyQuery } from '@vue/apollo-composable'
import { useAuth } from './modules/auth/composables/useAuth'
import { useOrgConfigStore } from './stores/orgConfig'
import { CONFIGURACIONES } from './modules/configuracion/graphql/configQueries'

// Si hay token guardado, recupera el usuario actual (nombre/roles) al arrancar.
const { cargarUsuarioActual } = useAuth()

// Carga los parámetros generales (incluye los de sesión) en orgConfig.
const orgConfig = useOrgConfigStore()
const { load: cargarConfig, onResult: onConfig } = useLazyQuery(CONFIGURACIONES, null, { fetchPolicy: 'cache-first' })
onConfig((r) => orgConfig.aplicarConfiguraciones(r.data?.configuraciones?.items ?? []))

onMounted(() => {
  cargarUsuarioActual()
  if (localStorage.getItem('auth_token')) cargarConfig()
})
</script>
