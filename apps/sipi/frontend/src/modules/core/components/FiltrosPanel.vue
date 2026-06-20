<!--
  FiltrosPanel.vue — panel de filtros ESTÁNDAR de la aplicación.

  Config-driven: cada vista declara sus facetas y este componente emite un objeto
  de filtros normalizado (claves camelCase = columnas) que useAgenteBase traduce a
  `filters:[FilterInput]` para el servidor.

  Layout: línea 1 = búsqueda genérica; línea 2 = resto de criterios (facetas como
  desplegables de checkboxes + cascada geográfica compacta + limpiar).

  Props:
    - conBusqueda     (Bool)  caja de búsqueda por texto (clave `search`)
    - conGeografia    (Bool)  cascada CCAA → Provincia → Municipio (store de geografía)
    - facetas         (Array) [{ key, label, opciones:[{id,nombre}], tipo:'checkboxes'|'select' }]
                              · checkboxes → multiselección → operador IN (clave = array de ids)
                              · select     → selección única  → operador EQ (clave = id)

  Emite: `change` con el objeto de filtros (solo claves con valor).
-->
<template>
  <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-3 space-y-2">
    <!-- Línea 1: búsqueda genérica -->
    <div v-if="conBusqueda" class="relative">
      <MagnifyingGlassIcon class="w-4 h-4 absolute left-3 top-2.5 text-gray-400 pointer-events-none" />
      <input
        v-model="estado.search"
        @input="emitChange"
        type="text"
        :placeholder="busquedaPlaceholder"
        class="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
      />
    </div>

    <!-- Línea 2: resto de criterios -->
    <div class="flex flex-wrap items-center gap-2">
      <template v-for="f in facetas" :key="f.key">
        <!-- Multiselección: desplegable de checkboxes -->
        <CheckboxDropdown
          v-if="(f.tipo || 'checkboxes') === 'checkboxes'"
          v-model="estado[f.key]"
          :options="f.opciones || []"
          :placeholder="f.label"
          @change="emitChange"
        />
        <!-- Selección única -->
        <select
          v-else
          v-model="estado[f.key]"
          @change="emitChange"
          class="px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">{{ f.label }}: todos</option>
          <option v-for="op in f.opciones" :key="op.id" :value="op.id">{{ op.nombre }}</option>
        </select>
      </template>

      <!-- Geografía: ancho razonable (modo compacto), no a pantalla completa -->
      <FiltroGeografico v-if="conGeografia" v-model="ubicacion" @change="emitChange" compact />

      <button
        type="button"
        @click="limpiar"
        class="ml-auto inline-flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
      >
        <FunnelIcon class="w-4 h-4" /> Limpiar
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { MagnifyingGlassIcon, FunnelIcon } from '@heroicons/vue/24/outline'
import FiltroGeografico from './FiltroGeografico.vue'
import CheckboxDropdown from './CheckboxDropdown.vue'

const props = defineProps({
  conBusqueda: { type: Boolean, default: true },
  busquedaLabel: { type: String, default: 'Búsqueda' },
  busquedaPlaceholder: { type: String, default: 'Nombre, NIF…' },
  conGeografia: { type: Boolean, default: false },
  facetas: { type: Array, default: () => [] }
})

const emit = defineEmits(['change'])

// Estado: search + una entrada por faceta (array para checkboxes, string para select).
const estado = reactive({ search: '' })
const inicializaFaceta = (f) => {
  if (estado[f.key] === undefined) {
    estado[f.key] = (f.tipo || 'checkboxes') === 'checkboxes' ? [] : ''
  }
}
props.facetas.forEach(inicializaFaceta)
// Las facetas pueden llegar de forma asíncrona (catálogos cargados tras el montaje).
watch(() => props.facetas, (fs) => fs.forEach(inicializaFaceta), { deep: false })

const ubicacion = ref({ comunidadAutonomaId: null, provinciaId: null, municipioId: null })

function emitChange() {
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
}

function limpiar() {
  estado.search = ''
  for (const f of props.facetas) {
    estado[f.key] = (f.tipo || 'checkboxes') === 'checkboxes' ? [] : ''
  }
  ubicacion.value = { comunidadAutonomaId: null, provinciaId: null, municipioId: null }
  emitChange()
}
</script>
