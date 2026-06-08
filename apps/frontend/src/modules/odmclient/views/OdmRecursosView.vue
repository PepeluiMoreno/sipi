<!-- modules/odm/views/OdmRecursosView.vue
     Consola de CLIENTE sobre ODM. SIPI es una Application consumidora:
     lista los recursos publicados en ODM (por sus publishers reales) y el
     estado de la suscripción de SIPI a cada uno. No define recursos propios.

     Habla con el backend de SIPI (BFF), no con ODM directamente:
     las credenciales/app_id de ODM viven en el servidor. Endpoints esperados:
       GET /api/odm/status              -> { online, app_id }
       GET /api/odm/resources           -> [{ id, name, publisher, fetcher,
                                              subscribed, last_run, state }]
     (Suscribir / refrescar se añaden detrás del OK de gobernanza ODM.)
-->
<template>
  <div class="p-6">
    <!-- Cabecera, al estilo de las demás vistas -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Recursos ODM</h1>
        <p class="text-sm text-gray-500">
          SIPI consume datos de referencia publicados en OpenDataManager.
          Esta consola muestra los recursos disponibles y a cuáles está suscrito SIPI.
        </p>
      </div>
      <span
        class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm border"
        :class="odm.online ? 'bg-green-50 text-green-700 border-green-200'
                           : 'bg-gray-100 text-gray-500 border-gray-200'"
      >
        <span class="w-2 h-2 rounded-full" :class="odm.online ? 'bg-green-500' : 'bg-gray-400'"></span>
        ODM {{ odm.online ? 'conectado' : 'sin conexión' }}
      </span>
    </div>

    <div v-if="loading" class="text-gray-500 text-sm">Cargando recursos de ODM…</div>
    <div v-else-if="error" class="text-red-600 text-sm">No se pudo consultar ODM: {{ error }}</div>

    <!-- Recursos agrupados por publisher (el dueño real del dato) -->
    <div v-else class="space-y-6">
      <div v-for="(items, publisher) in porPublisher" :key="publisher">
        <p class="px-1 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          {{ publisher }}
        </p>
        <div class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          <div v-for="r in items" :key="r.id"
               class="flex items-center justify-between px-4 py-3">
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{{ r.name }}</p>
              <p class="text-xs text-gray-500">{{ r.fetcher }}<span v-if="r.last_run"> · último refresco {{ r.last_run }}</span></p>
            </div>
            <span
              class="ml-4 shrink-0 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border"
              :class="r.subscribed ? 'bg-blue-50 text-blue-700 border-blue-200'
                                   : 'bg-gray-50 text-gray-500 border-gray-200'"
            >
              <span class="w-2 h-2 rounded-full" :class="r.subscribed ? 'bg-blue-500' : 'bg-gray-300'"></span>
              {{ r.subscribed ? 'Suscrito' : 'No suscrito' }}
            </span>
          </div>
        </div>
      </div>
      <p v-if="!recursos.length" class="text-sm text-gray-500">ODM no expone recursos todavía.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const loading = ref(true)
const error = ref(null)
const odm = ref({ online: false, app_id: null })
const recursos = ref([])

const porPublisher = computed(() => {
  const g = {}
  for (const r of recursos.value) (g[r.publisher || 'Sin publisher'] ??= []).push(r)
  return g
})

async function cargar() {
  loading.value = true; error.value = null
  try {
    const [s, r] = await Promise.all([
      fetch('/api/odm/status').then(x => x.json()),
      fetch('/api/odm/resources').then(x => x.json()),
    ])
    odm.value = s
    recursos.value = Array.isArray(r) ? r : []
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}
onMounted(cargar)
</script>
