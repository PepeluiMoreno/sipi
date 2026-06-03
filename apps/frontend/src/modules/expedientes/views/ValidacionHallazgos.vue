<template>
  <div class="max-w-4xl mx-auto p-6 space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Validación de hallazgos</h1>
      <p class="text-gray-600">
        Hallazgos propuestos por los servicios de descubrimiento (suscripciones a
        datasets de OpenDataManager). Ratifique para confirmarlos como expediente
        del inmueble, o descártelos.
      </p>
    </div>

    <p v-if="loading" class="text-gray-500 text-sm">Cargando hallazgos…</p>
    <p v-else-if="error" class="text-red-600 text-sm">{{ error }}</p>
    <p v-else-if="!hallazgos.length" class="text-gray-500 text-sm">
      No hay hallazgos pendientes de validación.
    </p>

    <div v-else class="space-y-3">
      <div v-for="h in hallazgos" :key="h.id"
           class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex justify-between items-start gap-4">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-gray-500">
                {{ h.tipo?.nombre || h.tipoExpedienteId }}
              </span>
              <span v-if="h.confianza" :class="badgeConfianza(h.confianza)">{{ h.confianza }}</span>
            </div>
            <p class="text-sm font-medium text-gray-900 mt-1">{{ h.titulo || '—' }}</p>
            <p v-if="h.inmueble" class="text-xs text-gray-500 mt-0.5">
              Inmueble: <router-link :to="`/inmuebles/${h.inmuebleId}`" class="text-indigo-600 hover:underline">{{ h.inmueble.nombre }}</router-link>
            </p>
            <p v-if="h.descripcion" class="text-sm text-gray-600 mt-1">{{ h.descripcion }}</p>
            <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
              <a v-if="h.enlace" :href="h.enlace" target="_blank" rel="noopener" class="text-indigo-600 hover:underline">fuente</a>
              <span v-if="h.referenciaExterna">ref: {{ h.referenciaExterna }}</span>
              <span v-if="h.importe != null" class="font-medium text-gray-700">{{ euros(h.importe) }}</span>
            </div>
          </div>
          <div class="flex flex-col gap-2 shrink-0">
            <button @click="accion(h, 'ratificar')" :disabled="ocupado === h.id"
                    class="px-3 py-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm disabled:opacity-50">
              Ratificar
            </button>
            <button @click="accion(h, 'descartar')" :disabled="ocupado === h.id"
                    class="px-3 py-1.5 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm disabled:opacity-50">
              Descartar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useExpedientes } from '../composables/useExpedientes'

const { listarHallazgos, ratificar, descartar, loading, error } = useExpedientes()
const hallazgos = ref([])
const ocupado = ref(null)

async function cargar() { hallazgos.value = await listarHallazgos() }
onMounted(cargar)

async function accion(h, tipo) {
  ocupado.value = h.id
  try {
    if (tipo === 'ratificar') await ratificar(h.id)
    else await descartar(h.id)
    hallazgos.value = hallazgos.value.filter(x => x.id !== h.id)
  } finally {
    ocupado.value = null
  }
}

function euros(v) {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(Number(v))
}
function badgeConfianza(c) {
  const base = 'text-[10px] px-1.5 py-0.5 rounded-full font-medium '
  if (c === 'ALTA') return base + 'bg-green-100 text-green-800'
  if (c === 'MEDIA') return base + 'bg-yellow-100 text-yellow-800'
  return base + 'bg-gray-100 text-gray-600'
}
</script>
