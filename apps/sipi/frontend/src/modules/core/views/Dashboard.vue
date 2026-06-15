<!-- src/modules/core/views/Dashboard.vue -->
<template>
  <div>
    <!-- Welcome banner -->
    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 mb-6 text-white">
      <h2 class="text-2xl font-bold mb-2">Bienvenido, {{ user?.name || 'Usuario' }}</h2>
      <p class="text-indigo-100">Panel de Control del Patrimonio Inmueble</p>
    </div>

    <!-- Stats grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-6">
      <div class="bg-white rounded-lg shadow p-6">
        <BuildingOfficeIcon class="w-10 h-10 text-blue-600 mb-2" />
        <p class="text-sm font-medium text-gray-600">Inmuebles Detectados</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.inmuebles_detectados }}</p>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <HomeIcon class="w-10 h-10 text-green-600 mb-2" />
        <p class="text-sm font-medium text-gray-600">Inmatriculados</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.inmatriculados }}</p>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <ShieldCheckIcon class="w-10 h-10 text-purple-600 mb-2" />
        <p class="text-sm font-medium text-gray-600">BICs Catalogados</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.bics_catalogados }}</p>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <ShoppingBagIcon class="w-10 h-10 text-yellow-600 mb-2" />
        <p class="text-sm font-medium text-gray-600">En Venta</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.en_venta }}</p>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <CheckCircleIcon class="w-10 h-10 text-green-600 mb-2" />
        <p class="text-sm font-medium text-gray-600">Vendidos</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.vendidos }}</p>
      </div>
    </div>

    <!-- Recent activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Últimos inmuebles -->
      <div class="bg-white rounded-lg shadow">
        <div class="p-6 border-b border-gray-200">
          <h3 class="font-semibold text-gray-900">Últimos Inmuebles</h3>
        </div>
        <div class="p-6">
          <div v-if="!ultimosInmuebles.length" class="text-center text-gray-500 py-8">
            <p>No hay inmuebles</p>
          </div>
          <div v-for="inmueble in ultimosInmuebles" :key="inmueble.id" class="p-3 bg-gray-50 rounded-lg mb-3">
            <p class="font-medium">{{ inmueble.nombre || inmueble.direccion || 'Sin denominación' }}</p>
            <p class="text-xs text-gray-500">{{ inmueble.direccion || '—' }}</p>
          </div>
        </div>
      </div>

      <!-- Actividad reciente -->
      <div class="bg-white rounded-lg shadow">
        <div class="p-6 border-b border-gray-200">
          <h3 class="font-semibold text-gray-900">Actividad Reciente</h3>
        </div>
        <div class="p-6">
          <div class="text-center text-gray-500 py-8">
            <p>No hay actividad reciente</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
// Importación CORREGIDA - core está dentro de modules
import { useAuthStore } from '../../../stores/auth'
import { GET_INMUEBLES } from '../../inmuebles/graphql/inmuebleQueries'
import {
  BuildingOfficeIcon,
  HomeIcon,
  ShieldCheckIcon,
  ShoppingBagIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'

// Usar el store de auth
const authStore = useAuthStore()
const user = ref(authStore.user || { name: 'Usuario' })

const stats = ref({
  inmuebles_detectados: 0,
  inmatriculados: 0,
  bics_catalogados: 0,
  en_venta: 0,
  vendidos: 0
})

const ultimosInmuebles = ref([])

const { resolveClient } = useApolloClient()

const loadDashboardData = async () => {
  try {
    const client = resolveClient()
    // Total + últimos inmuebles reales
    const { data } = await client.query({
      query: GET_INMUEBLES,
      variables: { limit: 5 },
      fetchPolicy: 'network-only'
    })
    stats.value.inmuebles_detectados = data?.inmuebles?.total ?? 0
    ultimosInmuebles.value = data?.inmuebles?.items ?? []

    // En venta (conteo real con filtro server-side)
    const { data: dv } = await client.query({
      query: GET_INMUEBLES,
      variables: { limit: 1, filters: [{ field: 'enVenta', operator: 'EQ', value: 'true' }] },
      fetchPolicy: 'network-only'
    })
    stats.value.en_venta = dv?.inmuebles?.total ?? 0
    // inmatriculados / bics / vendidos: pendientes de criterio real en el modelo (sin mock → 0)
  } catch (error) {
    console.error('Error cargando datos del dashboard:', error)
  }
}

onMounted(loadDashboardData)
</script>