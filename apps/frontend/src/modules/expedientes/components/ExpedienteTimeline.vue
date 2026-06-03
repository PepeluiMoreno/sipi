<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-900">Historial del inmueble</h2>
      <button
        @click="$emit('nuevo')"
        class="px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
      >+ Nuevo expediente</button>
    </div>

    <p v-if="loading" class="text-gray-500 text-sm">Cargando historial…</p>
    <p v-else-if="error" class="text-red-600 text-sm">{{ error }}</p>
    <p v-else-if="!expedientes.length" class="text-gray-500 text-sm">
      Sin expedientes registrados todavía.
    </p>

    <ol v-else class="relative border-l border-gray-200 ml-3">
      <li v-for="e in expedientes" :key="e.id" class="mb-6 ml-6">
        <span
          class="absolute -left-2.5 flex items-center justify-center w-5 h-5 rounded-full ring-4 ring-white"
          :class="colorPunto(e)"
        ></span>
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div class="flex justify-between items-start gap-3">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {{ e.tipo?.nombre || e.tipoExpedienteId }}
                </span>
                <span v-if="e.estado" :class="badgeEstado(e.estado)">{{ e.estado }}</span>
                <span v-if="e.confianza" :class="badgeConfianza(e.confianza)">{{ e.confianza }}</span>
              </div>
              <p class="text-sm font-medium text-gray-900 mt-1">{{ e.titulo || '—' }}</p>
              <p v-if="e.descripcion" class="text-sm text-gray-600 mt-1">{{ e.descripcion }}</p>
            </div>
            <div class="text-right shrink-0">
              <p class="text-xs text-gray-500">{{ fecha(e) }}</p>
              <p v-if="e.importe != null" class="text-sm font-semibold text-gray-900 mt-1">
                {{ euros(e.importe) }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 mt-3 text-xs">
            <a v-if="e.enlace" :href="e.enlace" target="_blank" rel="noopener"
               class="text-indigo-600 hover:underline">fuente</a>
            <span v-if="e.referenciaExterna" class="text-gray-400">ref: {{ e.referenciaExterna }}</span>
            <span class="flex-1"></span>
            <button @click="$emit('editar', e)" class="text-gray-500 hover:text-indigo-600">Editar</button>
            <button @click="$emit('eliminar', e)" class="text-gray-500 hover:text-red-600">Eliminar</button>
          </div>
        </div>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useExpedientes } from '../composables/useExpedientes'

const props = defineProps({ inmuebleId: { type: String, required: true } })
defineEmits(['nuevo', 'editar', 'eliminar'])

const { listarPorInmueble, loading, error } = useExpedientes()
const expedientes = ref([])

async function cargar() {
  if (!props.inmuebleId) return
  expedientes.value = await listarPorInmueble(props.inmuebleId)
}
defineExpose({ cargar })
onMounted(cargar)
watch(() => props.inmuebleId, cargar)

function fecha(e) {
  const f = e.fechaInicio || e.createdAt
  if (!f) return '—'
  const d = new Date(f)
  return isNaN(d) ? f : d.toLocaleDateString('es-ES')
}
function euros(v) {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(Number(v))
}
function colorPunto(e) {
  const c = e.tipo?.codigo || ''
  if (c === 'enajenacion') return 'bg-amber-500'
  if (c === 'secularizacion') return 'bg-purple-500'
  if (c === 'declaracion_ruina') return 'bg-red-500'
  if (c === 'subvencion') return 'bg-emerald-500'
  if (c === 'deteccion') return 'bg-sky-500'
  return 'bg-indigo-400'
}
function badgeEstado(estado) {
  const base = 'text-[10px] px-1.5 py-0.5 rounded-full font-medium '
  if (estado === 'propuesto') return base + 'bg-yellow-100 text-yellow-800'
  if (estado === 'confirmado') return base + 'bg-green-100 text-green-800'
  if (estado === 'descartado') return base + 'bg-gray-100 text-gray-500 line-through'
  return base + 'bg-gray-100 text-gray-700'
}
function badgeConfianza(c) {
  const base = 'text-[10px] px-1.5 py-0.5 rounded-full font-medium '
  if (c === 'ALTA') return base + 'bg-green-100 text-green-800'
  if (c === 'MEDIA') return base + 'bg-yellow-100 text-yellow-800'
  return base + 'bg-gray-100 text-gray-600'
}
</script>
