<template>
  <div 
    class="flex transition-all duration-300 ease-in-out bg-white border-r border-gray-200"
    :class="isCollapsed ? 'w-16' : 'w-80'"
  >
    <!-- Botón colapsar/expandir -->
    <div class="flex flex-col items-center py-4">
      <button
        @click="$emit('toggle-sidebar')"
        class="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
        :title="isCollapsed ? 'Expandir sidebar' : 'Colapsar sidebar'"
      >
        <Bars3Icon class="w-5 h-5" />
      </button>
    </div>

    <!-- Contenido cuando está expandido -->
    <div v-if="!isCollapsed" class="flex-1 flex flex-col h-full">
      
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Filtros</h2>
      </div>

      <!-- Contenido de filtros -->
      <div class="flex-1 overflow-y-auto">
        <div class="p-4 space-y-6">
          
          <!-- Búsqueda -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
            <div class="relative">
              <MagnifyingGlassIcon class="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                v-model="localFilters.search"
                type="text"
                placeholder="Nombre o dirección..."
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                @keyup.enter="aplicarFiltros"
              />
            </div>
          </div>

          <!-- Provincia -->
          <div>
            <h3 class="text-sm font-medium text-gray-900 mb-3">Provincia</h3>
            <select
              v-model="localFilters.provincia"
              class="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              @change="onProvinciaChange"
            >
              <option value="">Todas las provincias</option>
              <option v-for="provincia in provinciasUnicas" :key="provincia" :value="provincia">
                {{ provincia }}
              </option>
            </select>
          </div>

          <!-- Localidad -->
          <div>
            <h3 class="text-sm font-medium text-gray-900 mb-3">Localidad</h3>
            <select
              v-model="localFilters.localidad"
              class="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              @change="handleFiltersChange"
            >
              <option value="">Todas las localidades</option>
              <option v-for="localidad in localidadesFiltradas" :key="localidad" :value="localidad">
                {{ localidad }}
              </option>
            </select>
          </div>

          <!-- Estado -->
          <div>
            <h3 class="text-sm font-medium text-gray-900 mb-3">Estado</h3>
            <div class="space-y-2">
              <label v-for="estado in estados" :key="estado.key" class="flex items-center cursor-pointer">
                <input
                  :checked="(localFilters.estados || []).includes(estado.key)"
                  type="checkbox"
                  :value="estado.key"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  @change="onEstadoChange(estado.key, $event.target.checked)"
                />
                <span class="ml-3 text-sm text-gray-700">{{ estado.label }}</span>
              </label>
            </div>
          </div>

        </div>

        <!-- Botones - Ahora dentro del área scrollable pero pegados abajo -->
        <div class="p-4 border-t border-gray-200 bg-gray-50 mt-auto">
          <div class="space-y-2">
            <button 
              @click="aplicarFiltros"
              class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            >
              Aplicar Filtros
            </button>
            <button 
              @click="limpiarFiltros"
              class="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  Bars3Icon,
  MagnifyingGlassIcon
} from '@heroicons/vue/24/outline'
import { mockInmuebles } from '@/mocks/index.js'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({})
  },
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['filters-change', 'toggle-sidebar'])

// Estados disponibles
const estados = [
  { key: 'no_investigado', label: 'No investigado' },
  { key: 'inmatriculado', label: 'Inmatriculado' },
  { key: 'vendido', label: 'Vendido' },
  { key: 'en_venta', label: 'En venta' },
  { key: 'bic', label: 'BIC' }
]

// Datos geográficos únicos
const provinciasUnicas = computed(() => {
  const provincias = [...new Set(mockInmuebles.map(inmueble => inmueble.provincia))]
  return provincias.sort()
})

const todasLasLocalidades = computed(() => {
  const localidades = [...new Set(mockInmuebles.map(inmueble => inmueble.localidad))]
  return localidades.sort()
})

const localidadesFiltradas = computed(() => {
  if (!localFilters.value.provincia) {
    return todasLasLocalidades.value
  }
  return mockInmuebles
    .filter(inmueble => inmueble.provincia === localFilters.value.provincia)
    .map(inmueble => inmueble.localidad)
    .filter((localidad, index, array) => array.indexOf(localidad) === index)
    .sort()
})

// Filtros locales
const localFilters = ref({
  search: '',
  provincia: '',
  localidad: '',
  estados: []
})

// Sincronizar con props
watch(() => props.filters, (newFilters) => {
  localFilters.value = { 
    search: newFilters.search || '',
    provincia: newFilters.provincia || '',
    localidad: newFilters.localidad || '',
    estados: newFilters.estados || []
  }
}, { immediate: true, deep: true })

const onProvinciaChange = () => {
  // Al cambiar provincia, limpiar localidad
  localFilters.value.localidad = ''
  handleFiltersChange()
}

const handleFiltersChange = () => {
  // Solo actualiza los filtros locales, no aplica
  // El usuario debe hacer click en "Aplicar Filtros"
}

const onEstadoChange = (estadoKey, checked) => {
  const estadosActuales = localFilters.value.estados || []
  
  if (checked) {
    // Agregar estado si no existe
    if (!estadosActuales.includes(estadoKey)) {
      localFilters.value.estados = [...estadosActuales, estadoKey]
    }
  } else {
    // Remover estado
    localFilters.value.estados = estadosActuales.filter(e => e !== estadoKey)
  }
  handleFiltersChange()
}

const aplicarFiltros = () => {
  emit('filters-change', { ...localFilters.value })
}

const limpiarFiltros = () => {
  localFilters.value = {
    search: '',
    provincia: '',
    localidad: '',
    estados: []
  }
  emit('filters-change', { ...localFilters.value })
}
</script>