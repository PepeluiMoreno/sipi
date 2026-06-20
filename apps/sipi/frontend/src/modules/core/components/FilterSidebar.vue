<!--
  FilterSidebar.vue — panel de filtros VERTICAL, escamoteable. Estándar de la app.

  Config-driven (misma API de facetas que FiltrosPanel → drop-in). Emite `change`
  con un objeto normalizado (claves camelCase = columnas) que useAgenteBase traduce
  a filters:[FilterInput] (array→IN, escalar→EQ).

  META-REGLA de diseño (al vuelo):
    · faceta checkboxes con ≤ 5 opciones → columna de checkboxes SIEMPRE visible
    · faceta checkboxes con > 5 opciones → CheckboxDropdown (desplegable)

  Props:
    conBusqueda (Bool)  caja de búsqueda (clave `search`)
    conGeografia (Bool) cascada CCAA→Prov→Muni (vertical, vía geografiaStore)
    facetas (Array) [{ key, label, opciones:[{id,nombre}], tipo:'checkboxes'|'select', allLabel }]
  Emite: `change` (objeto de filtros, solo claves con valor).
-->
<template>
  <aside v-if="abierto" class="w-72 shrink-0 bg-white border-r border-gray-200 flex flex-col min-h-0">
    <div class="shrink-0 h-11 px-3 flex items-center justify-between border-b border-gray-200">
      <h2 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <FunnelIcon class="w-4 h-4 text-gray-400" /> Filtros
      </h2>
      <button @click="abierto = false" class="p-1 rounded hover:bg-gray-100 text-gray-400" title="Ocultar filtros">
        <ChevronLeftIcon class="w-4 h-4" />
      </button>
    </div>

    <div class="flex-1 min-h-0 overflow-auto p-3 space-y-4">
      <div v-if="conBusqueda">
        <label class="block text-xs font-medium text-gray-500 mb-1">{{ busquedaLabel }}</label>
        <input v-model="estado.search" @input="emitChange" type="text" :placeholder="busquedaPlaceholder"
               class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" />
      </div>

      <div v-for="f in facetas" :key="f.key">
        <label class="block text-xs font-medium text-gray-500 mb-1">{{ f.label }}</label>

        <!-- selección única -->
        <select v-if="f.tipo === 'select'" v-model="estado[f.key]" @change="emitChange"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
          <option value="">{{ f.allLabel || 'Todos' }}</option>
          <option v-for="op in f.opciones" :key="op.id" :value="op.id">{{ op.nombre }}</option>
        </select>

        <!-- > 5 opciones → desplegable para elegir + seleccionados como checkboxes fijos -->
        <div v-else-if="(f.opciones || []).length > 5">
          <CheckboxDropdown v-model="estado[f.key]" :options="f.opciones || []"
                            :placeholder="f.label" static-label @change="emitChange" />
          <div v-if="(estado[f.key] || []).length" class="mt-1.5 space-y-1">
            <label v-for="val in estado[f.key]" :key="val"
                   class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" :value="val" v-model="estado[f.key]" @change="emitChange"
                     class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
              <span class="truncate">{{ etiquetaOpcion(f, val) }}</span>
            </label>
          </div>
        </div>

        <!-- ≤ 5 opciones → columna de checkboxes siempre visible -->
        <div v-else class="space-y-1">
          <label v-if="(f.opciones || []).length"
                 class="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
            <input type="checkbox" :checked="todasFaceta(f)" @change="toggleTodasFaceta(f)"
                   class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
            <span>Cualquiera</span>
          </label>
          <label v-for="op in (f.opciones || [])" :key="op.id"
                 class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input type="checkbox" :value="op.id" v-model="estado[f.key]" @change="emitChange"
                   class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
            <span class="truncate">{{ op.nombre }}</span>
          </label>
          <p v-if="!(f.opciones || []).length" class="text-xs text-gray-400">Sin opciones</p>
        </div>
      </div>

      <div v-if="conGeografia">
        <label class="block text-xs font-medium text-gray-500 mb-1">Ubicación</label>
        <FiltroGeografico v-model="ubicacion" vertical @change="emitChange" />
      </div>
    </div>

    <!-- Selección activa (literal, estilo SIGA) -->
    <div v-if="chips.length" class="shrink-0 px-3 py-2 border-t border-gray-200">
      <div class="flex flex-wrap gap-1.5">
        <span v-for="c in chips" :key="c.id"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs border border-indigo-100">
          {{ c.label }}
          <button type="button" class="leading-none hover:text-indigo-900" @click="quitar(c)">×</button>
        </span>
      </div>
    </div>

    <div class="shrink-0 p-3 border-t border-gray-200">
      <button type="button" @click="limpiar"
              class="w-full inline-flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg">
        <FunnelIcon class="w-4 h-4" /> Limpiar
      </button>
    </div>
  </aside>

  <button v-else @click="abierto = true" title="Mostrar filtros"
          class="self-start mt-2 bg-white border border-gray-200 border-l-0 rounded-r p-2 text-gray-500 hover:bg-gray-50 shrink-0">
    <FunnelIcon class="w-4 h-4" />
  </button>
</template>

<script setup>
import { reactive, ref, computed, watch, onBeforeUnmount } from 'vue'
import { FunnelIcon, ChevronLeftIcon } from '@heroicons/vue/24/outline'
import FiltroGeografico from './FiltroGeografico.vue'
import CheckboxDropdown from './CheckboxDropdown.vue'
import { useGeografiaStore } from '@/stores/geografia'

const props = defineProps({
  conBusqueda: { type: Boolean, default: true },
  busquedaLabel: { type: String, default: 'Búsqueda' },
  busquedaPlaceholder: { type: String, default: 'Nombre, NIF…' },
  conGeografia: { type: Boolean, default: false },
  facetas: { type: Array, default: () => [] }
})
const emit = defineEmits(['change'])

const abierto = ref(true)
const geografiaStore = useGeografiaStore()

const estado = reactive({ search: '' })
const inicializaFaceta = (f) => {
  if (estado[f.key] === undefined) estado[f.key] = (f.tipo || 'checkboxes') === 'checkboxes' ? [] : ''
}
props.facetas.forEach(inicializaFaceta)
watch(() => props.facetas, (fs) => fs.forEach(inicializaFaceta), { deep: false })

const ubicacion = ref({ comunidadAutonomaId: null, provinciaId: null, municipioId: null })

const etiquetaOpcion = (f, val) => (f.opciones || []).find(o => o.id === val)?.nombre || val

// "Cualquiera": marcada cuando están todas; alterna todas / ninguna.
const todasFaceta = (f) => {
  const ops = f.opciones || []
  return ops.length > 0 && (estado[f.key] || []).length === ops.length
}
const toggleTodasFaceta = (f) => {
  estado[f.key] = todasFaceta(f) ? [] : (f.opciones || []).map(o => o.id)
  emitChange()
}

// Debounce del refetch: la cascada geográfica (provincia → municipio) y el teclear
// en la búsqueda disparan varios cambios seguidos; se coalescen en una sola consulta.
let timer = null
const emitChange = () => {
  clearTimeout(timer)
  timer = setTimeout(() => {
    const payload = {}
    if (props.conBusqueda && estado.search?.trim()) payload.search = estado.search.trim()
    for (const f of props.facetas) {
      const v = estado[f.key]
      if (Array.isArray(v)) { if (v.length) payload[f.key] = v }
      else if (v) payload[f.key] = v
    }
    if (props.conGeografia) {
      for (const k of ['comunidadAutonomaId', 'provinciaId', 'municipioId']) {
        if (ubicacion.value[k]) payload[k] = ubicacion.value[k]
      }
    }
    emit('change', payload)
  }, 280)
}
onBeforeUnmount(() => clearTimeout(timer))

const chips = computed(() => {
  const out = []
  if (props.conBusqueda && estado.search?.trim()) out.push({ id: 'search', kind: 'search', label: `“${estado.search.trim()}”` })
  for (const f of props.facetas) {
    const v = estado[f.key]
    if (Array.isArray(v)) continue // facetas de checkboxes: se ven inline, no como chip
    if (v) {
      const op = (f.opciones || []).find(o => String(o.id) === String(v))
      out.push({ id: f.key, kind: 'scalar', key: f.key, label: `${f.label}: ${op?.nombre || v}` })
    }
  }
  if (props.conGeografia) {
    const nombre =
      geografiaStore.municipios.find(m => m.id === ubicacion.value.municipioId)?.nombre ||
      geografiaStore.provincias.find(p => p.id === ubicacion.value.provinciaId)?.nombre ||
      geografiaStore.comunidadesAutonomas.find(c => c.id === ubicacion.value.comunidadAutonomaId)?.nombre
    if (nombre) out.push({ id: 'geo', kind: 'geo', label: nombre })
  }
  return out
})

const quitar = (c) => {
  if (c.kind === 'search') estado.search = ''
  else if (c.kind === 'geo') ubicacion.value = { comunidadAutonomaId: null, provinciaId: null, municipioId: null }
  else if (c.kind === 'array') estado[c.key] = estado[c.key].filter(x => x !== c.val)
  else estado[c.key] = ''
  emitChange()
}

const limpiar = () => {
  estado.search = ''
  for (const f of props.facetas) estado[f.key] = (f.tipo || 'checkboxes') === 'checkboxes' ? [] : ''
  ubicacion.value = { comunidadAutonomaId: null, provinciaId: null, municipioId: null }
  emitChange()
}
</script>
