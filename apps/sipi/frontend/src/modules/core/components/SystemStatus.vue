<template>
  <div class="relative mb-4">
    <div
      class="flex items-center justify-between px-2 py-1.5 rounded-lg transition-all duration-300 cursor-pointer bg-indigo-800 hover:bg-indigo-700"
      @click="toggleDetails"
    >
      <div class="flex items-center">
        <div class="w-2 h-2 rounded-full mr-2 animate-pulse" :class="dotClasses"></div>
        <span class="text-[10px] font-medium text-indigo-100">{{ statusText }}</span>
      </div>

      <svg
        class="w-3 h-3 transition-transform text-indigo-300"
        :class="{ 'transform rotate-180': showDetails }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>

    <div
      v-if="showDetails"
      class="absolute bottom-full left-0 right-0 mb-2 bg-indigo-900 rounded-lg shadow-xl border border-indigo-700 p-2.5 z-50"
    >
      <div class="space-y-1.5">
        <div>
          <h4 class="text-[10px] font-semibold mb-1.5 text-indigo-200">Estado del Sistema</h4>
          <div class="space-y-1">
            <div class="flex justify-between text-[10px]">
              <span class="text-indigo-400">API REST</span>
              <span :class="apiStatus ? 'text-green-400' : 'text-red-400'">
                {{ apiStatus ? 'Online' : 'Offline' }}
              </span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span class="text-indigo-400">GraphQL</span>
              <span :class="graphqlStatus ? 'text-green-400' : 'text-red-400'">
                {{ graphqlStatus ? 'Online' : 'Offline' }}
              </span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span class="text-indigo-400">Base de Datos</span>
              <span :class="dbStatus ? 'text-green-400' : 'text-red-400'">
                {{ dbStatus ? 'Conectada' : 'Desconectada' }}
              </span>
            </div>
          </div>
        </div>

        <div class="pt-1.5 border-t border-indigo-700">
          <div class="text-[10px] text-indigo-300 space-y-0.5">
            <div class="flex justify-between">
              <span>Último check:</span>
              <span>{{ lastChecked }}</span>
            </div>
            <div class="flex justify-between">
              <span>Tiempo respuesta:</span>
              <span>{{ responseTime }}ms</span>
            </div>
            <div class="flex justify-between">
              <span>Uptime API:</span>
              <span>{{ apiUptime }}</span>
            </div>
          </div>
        </div>

        <button
          @click="checkStatus"
          class="w-full mt-1.5 px-2 py-1 text-[10px] bg-indigo-700 hover:bg-indigo-600 text-indigo-100 rounded transition-colors"
          :disabled="checking"
        >
          <span v-if="checking" class="flex items-center justify-center">
            <svg class="animate-spin -ml-1 mr-2 h-2.5 w-2.5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Verificando...
          </span>
          <span v-else>Verificar Estado</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8040'

const apiStatus = ref(false)
const graphqlStatus = ref(false)
const dbStatus = ref(false)
const checking = ref(false)
const showDetails = ref(false)
const lastChecked = ref('Never')
const responseTime = ref(0)
const apiUptime = ref('--:--:--')

const overallStatus = computed(() => {
  return apiStatus.value && graphqlStatus.value && dbStatus.value
})

const dotClasses = computed(() => {
  if (checking.value) return 'bg-yellow-400'
  return overallStatus.value ? 'bg-green-400' : 'bg-red-400'
})

const statusText = computed(() => {
  if (checking.value) return 'Verificando...'
  return overallStatus.value ? 'Sistema Online' : 'Problemas'
})

// Función para formatear segundos a HH:MM:SS
function formatUptime(seconds) {
  if (!seconds) return '--:--:--'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

async function checkStatus() {
  checking.value = true
  
  try {
    const startTime = Date.now()
    
    // 1. Verificar API REST (usar el endpoint /health)
    try {
      const apiResponse = await fetch(`${backendUrl}/health`)
      if (apiResponse.ok) {
        const data = await apiResponse.json()
        apiStatus.value = data.status === 'healthy'
        apiUptime.value = formatUptime(data.uptime_seconds)
      } else {
        apiStatus.value = false
      }
    } catch {
      apiStatus.value = false
    }
    
    // 2. Verificar GraphQL
    try {
      const graphqlResponse = await fetch(`${backendUrl}/graphql`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: '{ __typename }' }),
        // Agregar timeout para no esperar demasiado
        signal: AbortSignal.timeout(3000)
      })
      graphqlStatus.value = graphqlResponse.ok
    } catch {
      graphqlStatus.value = false
    }
    
    // 3. Verificar Base de Datos (usar el endpoint /api/health/db)
    try {
      const dbResponse = await fetch(`${backendUrl}/api/health/db`, {
        signal: AbortSignal.timeout(3000)
      })
      if (dbResponse.ok) {
        const data = await dbResponse.json()
        dbStatus.value = data.database?.connected || data.connected || false
      } else {
        dbStatus.value = false
      }
    } catch {
      dbStatus.value = false
    }
    
    responseTime.value = Date.now() - startTime
    lastChecked.value = new Date().toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
    
  } catch (error) {
    console.error('Status check failed:', error)
    // Si hay un error general, marcar todo como offline
    apiStatus.value = false
    graphqlStatus.value = false
    dbStatus.value = false
  } finally {
    checking.value = false
  }
}

function toggleDetails() {
  showDetails.value = !showDetails.value
}

onMounted(() => {
  // Verificar inmediatamente al montar
  checkStatus()
  
  // Configurar verificación periódica cada 30 segundos
  const interval = setInterval(checkStatus, 30000)
  
  onBeforeUnmount(() => {
    clearInterval(interval)
  })
})
</script>
