<template>
  <div class="relative bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-full flex flex-col">
    <!-- Tabla -->
    <div v-if="hasItems" ref="tablaRef" class="flex-1 min-h-0 overflow-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50 sticky top-0 z-10">
          <tr>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NIF</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Localidad</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="entidad in filas" :key="entidad.id"
              @click="$emit('ver', entidad.id)"
              :class="['cursor-pointer', entidad.id === selectedId ? 'bg-indigo-50' : 'hover:bg-gray-50']">
            <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{{ entidad.nombre }}</td>
            <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">{{ entidad.tipoEntidad?.nombre || '-' }}</td>
            <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{{ entidad.nif || '-' }}</td>
            <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{{ entidad.municipioSede?.nombre || '-' }}</td>
            <td class="px-4 py-2 whitespace-nowrap">
              <span :class="[entidad.activa ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700',
                             'px-2 inline-flex text-xs leading-5 rounded-full']">
                {{ entidad.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td class="px-4 py-2 whitespace-nowrap text-right text-sm">
              <button @click.stop="$emit('ver', entidad.id)" class="text-gray-400 hover:text-gray-700 mr-2" title="Consultar">
                <EyeIcon class="w-4 h-4 inline" />
              </button>
              <button @click.stop="$emit('edit', entidad.id)" class="text-indigo-600 hover:text-indigo-900 mr-2" title="Editar">
                <PencilIcon class="w-4 h-4 inline" />
              </button>
              <button @click.stop="$emit('delete', entidad.id)" class="text-red-600 hover:text-red-900" title="Eliminar">
                <TrashIcon class="w-4 h-4 inline" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Estado vacío -->
    <div v-else-if="!loading" class="flex-1 p-12 text-center">
      <BuildingLibraryIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500">No se encontraron entidades religiosas</p>
    </div>

    <!-- Loading: overlay (no ocupa espacio en el flex → no provoca recálculo de altura) -->
    <div v-if="loading" class="absolute top-2 right-2 z-20">
      <ArrowPathIcon class="w-5 h-5 animate-spin text-gray-400" />
    </div>

    <!-- Pie: paginación a altura (oculto al colapsar a un registro) -->
    <div v-if="hasItems && !selectedId"
         class="shrink-0 p-2 border-t border-gray-200 flex justify-between items-center text-sm text-gray-600">
      <div>{{ rango }} de {{ total.toLocaleString('es-ES') }}</div>
      <div class="flex items-center gap-2">
        <button @click="$emit('change-page', page - 1)" :disabled="page <= 1"
                class="px-2 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50">Anterior</button>
        <span class="tabular-nums">{{ page }} / {{ totalPaginas }}</span>
        <button @click="$emit('change-page', page + 1)" :disabled="page >= totalPaginas"
                class="px-2 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50">Siguiente</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onBeforeUnmount, watch } from 'vue'
import { BuildingLibraryIcon, ArrowPathIcon, EyeIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 15 },
  selectedId: { type: [String, null], default: null }
})
const emit = defineEmits(['create', 'ver', 'edit', 'delete', 'change-page', 'update:pageSize'])

const hasItems = computed(() => props.items.length > 0)
// Al seleccionar, la lista se encoge a solo el registro elegido.
const filas = computed(() => props.selectedId ? props.items.filter(i => i.id === props.selectedId) : props.items)

const totalPaginas = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const rango = computed(() => {
  if (!props.total) return 'Sin resultados'
  const desde = (props.page - 1) * props.pageSize + 1
  const hasta = Math.min(props.page * props.pageSize, props.total)
  return `${desde.toLocaleString('es-ES')}–${hasta.toLocaleString('es-ES')}`
})

// Paginación a altura: nº de filas que caben sin scroll (ResizeObserver sobre el contenedor).
const tablaRef = ref(null)
const ROW_H = 37   // alto aproximado de fila (px-4 py-2)
const HEAD_H = 34
const recalcular = () => {
  if (props.selectedId || props.loading) return // colapsado o cargando: no recalcular
  const h = tablaRef.value?.clientHeight || 0
  if (!h) return
  const filasCaben = Math.max(5, Math.floor((h - HEAD_H) / ROW_H))
  // Histéresis: solo cambiar si difiere en ≥2 filas (evita oscilación ±1 = temblor).
  if (Math.abs(filasCaben - props.pageSize) >= 2) emit('update:pageSize', filasCaben)
}
// Coalesce las notificaciones del ResizeObserver en un frame (rompe el bucle de resize).
let rafId = null
const recalcularCoalesced = () => {
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => { rafId = null; recalcular() })
}
const ro = new ResizeObserver(recalcularCoalesced)
// Atar el observer cuando la tabla aparece (puede montar vacía durante la carga).
watch(tablaRef, (el) => {
  ro.disconnect()
  if (el) { ro.observe(el); recalcularCoalesced() }
}, { flush: 'post' })
watch(() => props.selectedId, (v) => { if (!v) recalcularCoalesced() })
onBeforeUnmount(() => { ro.disconnect(); if (rafId) cancelAnimationFrame(rafId) })
</script>
