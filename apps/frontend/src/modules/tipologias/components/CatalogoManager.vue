<template>
  <div class="catalogo-manager">
    <!-- Header del tipología -->
    <div class="mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">{{ catalogoConfig.nombre }}</h2>
          <p class="text-sm text-gray-600">{{ catalogoConfig.descripcion }}</p>
        </div>
        <div class="flex space-x-3">
          <button
            @click="exportarDatos"
            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center text-sm"
          >
            <ArrowDownTrayIcon class="w-4 h-4 mr-2" />
            Exportar
          </button>
          <button
            @click="$emit('nuevo-item')"
            class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center text-sm"
          >
            <PlusIcon class="w-4 h-4 mr-2" />
            Nuevo {{ catalogoConfig.singular }}
          </button>
        </div>
      </div>
    </div>

    <!-- Búsqueda y filtros -->
    <div class="mb-6 bg-white p-4 rounded-lg shadow-sm border">
      <div class="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="`Buscar ${catalogoConfig.plural}...`"
              class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
            <MagnifyingGlassIcon class="w-5 h-5 text-gray-400 absolute left-3 top-2.5" />
          </div>
        </div>
        
        <div class="flex space-x-4">
          <select
            v-model="filters.estado"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          >
            <option value="">Todos los estados</option>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </select>
          
          <select
            v-model="itemsPorPagina"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          >
            <option value="10">10 por página</option>
            <option value="25">25 por página</option>
            <option value="50">50 por página</option>
            <option value="100">100 por página</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Estadísticas rápidas -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white p-4 rounded-lg shadow-sm border">
        <p class="text-sm font-medium text-gray-600">Total</p>
        <p class="text-2xl font-bold text-gray-900">{{ items.length }}</p>
      </div>
      <div class="bg-white p-4 rounded-lg shadow-sm border">
        <p class="text-sm font-medium text-gray-600">Activos</p>
        <p class="text-2xl font-bold text-green-600">{{ itemsActivos }}</p>
      </div>
      <div class="bg-white p-4 rounded-lg shadow-sm border">
        <p class="text-sm font-medium text-gray-600">Inactivos</p>
        <p class="text-2xl font-bold text-red-600">{{ itemsInactivos }}</p>
      </div>
      <div class="bg-white p-4 rounded-lg shadow-sm border">
        <p class="text-sm font-medium text-gray-600">Filtrados</p>
        <p class="text-2xl font-bold text-indigo-600">{{ itemsFiltrados.length }}</p>
      </div>
    </div>

    <!-- Tabla de items -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th 
                v-for="columna in columnas" 
                :key="columna.key"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                @click="ordenarPor(columna.key)"
              >
                <div class="flex items-center">
                  {{ columna.label }}
                  <ChevronUpDownIcon 
                    v-if="orden.columna === columna.key"
                    class="w-4 h-4 ml-1"
                    :class="orden.direccion === 'asc' ? 'text-indigo-600' : 'text-gray-400'"
                  />
                </div>
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr 
              v-for="item in itemsPaginados" 
              :key="item.id"
              class="hover:bg-gray-50 transition-colors"
            >
              <td 
                v-for="columna in columnas" 
                :key="columna.key"
                class="px-6 py-4 whitespace-nowrap text-sm"
                :class="getCellClass(item, columna.key)"
              >
                <template v-if="columna.tipo === 'estado'">
                  <span 
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getEstadoClass(item.estado)"
                  >
                    {{ getEstadoLabel(item.estado) }}
                  </span>
                </template>
                <template v-else-if="columna.tipo === 'fecha'">
                  {{ formatFecha(getItemValue(item, columna.key)) }}
                </template>
                <template v-else-if="columna.tipo === 'boolean'">
                  <CheckIcon v-if="getItemValue(item, columna.key)" class="w-4 h-4 text-green-600" />
                  <XMarkIcon v-else class="w-4 h-4 text-red-600" />
                </template>
                <template v-else>
                  {{ getItemValue(item, columna.key) }}
                </template>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex justify-end space-x-2">
                  <button
                    @click="$emit('editar-item', item)"
                    class="text-indigo-600 hover:text-indigo-900 flex items-center"
                    title="Editar"
                  >
                    <PencilIcon class="w-4 h-4" />
                  </button>
                  <button
                    @click="$emit('eliminar-item', item)"
                    class="text-red-600 hover:text-red-900 flex items-center"
                    title="Eliminar"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                  <button
                    v-if="catalogoConfig.puedeActivar"
                    @click="toggleEstado(item)"
                    class="text-gray-600 hover:text-gray-900 flex items-center"
                    :title="item.estado === 'activo' ? 'Desactivar' : 'Activar'"
                  >
                    <PowerIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Estado vacío -->
      <div v-if="itemsFiltrados.length === 0" class="text-center py-12">
        <DocumentTextIcon class="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          No hay {{ catalogoConfig.plural.toLowerCase() }}
        </h3>
        <p class="text-gray-600 mb-4 max-w-md mx-auto">
          {{ searchQuery || filters.estado ? 
            'No se encontraron resultados para los filtros aplicados.' : 
            `Comience agregando el primer ${catalogoConfig.singular.toLowerCase()} al sistema.` 
          }}
        </p>
        <button
          @click="$emit('nuevo-item')"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 inline-flex items-center"
        >
          <PlusIcon class="w-4 h-4 mr-2" />
          Crear {{ catalogoConfig.singular }}
        </button>
        <button
          v-if="searchQuery || filters.estado"
          @click="limpiarFiltros"
          class="ml-3 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
        >
          Limpiar filtros
        </button>
      </div>

      <!-- Paginación -->
      <div v-if="itemsFiltrados.length > 0" class="bg-white px-6 py-3 border-t border-gray-200">
        <div class="flex flex-col md:flex-row items-center justify-between space-y-3 md:space-y-0">
          <div class="text-sm text-gray-700">
            Mostrando {{ inicioPagina }}-{{ finPagina }} de {{ itemsFiltrados.length }} {{ catalogoConfig.plural.toLowerCase() }}
          </div>
          <div class="flex items-center space-x-2">
            <button
              :disabled="pagination.page === 1"
              @click="pagination.page--"
              class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              <ChevronLeftIcon class="w-4 h-4" />
            </button>
            
            <span class="px-3 py-1 text-sm text-gray-700">
              Página {{ pagination.page }} de {{ totalPaginas }}
            </span>
            
            <button
              :disabled="pagination.page >= totalPaginas"
              @click="pagination.page++"
              class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              <ChevronRightIcon class="w-4 h-4" />
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
  PlusIcon, 
  MagnifyingGlassIcon, 
  DocumentTextIcon,
  ArrowDownTrayIcon,
  ChevronUpDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PencilIcon,
  TrashIcon,
  PowerIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  catalogoConfig: {
    type: Object,
    required: true,
    default: () => ({
      id: '',
      nombre: '',
      descripcion: '',
      singular: 'Elemento',
      plural: 'Elementos',
      puedeActivar: true
    })
  },
  items: {
    type: Array,
    default: () => []
  },
  columnas: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['nuevo-item', 'editar-item', 'eliminar-item', 'estado-cambiado'])

// Estado reactivo
const searchQuery = ref('')
const filters = ref({
  estado: ''
})
const itemsPorPagina = ref('10')
const orden = ref({
  columna: 'nombre',
  direccion: 'asc'
})

const pagination = ref({
  page: 1,
  pageSize: 10
})

// Watch para resetear paginación cuando cambian los filtros
watch([searchQuery, filters], () => {
  pagination.value.page = 1
})

watch(itemsPorPagina, (newValue) => {
  pagination.value.pageSize = parseInt(newValue)
  pagination.value.page = 1
})

// Computed properties
const itemsActivos = computed(() => 
  props.items.filter(item => item.estado === 'activo').length
)

const itemsInactivos = computed(() => 
  props.items.filter(item => item.estado === 'inactivo').length
)

// Items filtrados y ordenados
const itemsFiltrados = computed(() => {
  let filtered = props.items

  // Filtrar por búsqueda
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item => 
      Object.values(item).some(value => 
        value && String(value).toLowerCase().includes(query)
      )
    )
  }

  // Filtrar por estado
  if (filters.value.estado) {
    filtered = filtered.filter(item => item.estado === filters.value.estado)
  }

  // Ordenar
  if (orden.value.columna) {
    filtered = [...filtered].sort((a, b) => {
      const aVal = getItemValue(a, orden.value.columna)
      const bVal = getItemValue(b, orden.value.columna)
      
      if (aVal < bVal) return orden.value.direccion === 'asc' ? -1 : 1
      if (aVal > bVal) return orden.value.direccion === 'asc' ? 1 : -1
      return 0
    })
  }

  return filtered
})

// Items paginados
const itemsPaginados = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return itemsFiltrados.value.slice(start, end)
})

// Información de paginación
const totalPaginas = computed(() => 
  Math.ceil(itemsFiltrados.value.length / pagination.value.pageSize)
)

const inicioPagina = computed(() => 
  (pagination.value.page - 1) * pagination.value.pageSize + 1
)

const finPagina = computed(() => 
  Math.min(pagination.value.page * pagination.value.pageSize, itemsFiltrados.value.length)
)

// Métodos
const getItemValue = (item, key) => {
  const keys = key.split('.')
  let value = item
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k]
    } else {
      return ''
    }
  }
  return value || ''
}

const getCellClass = (item, key) => {
  const baseClass = 'px-6 py-4 whitespace-nowrap text-sm'
  if (key === 'nombre' || key === 'descripcion') {
    return `${baseClass} text-gray-900 font-medium`
  }
  return `${baseClass} text-gray-500`
}

const getEstadoClass = (estado) => {
  const classes = {
    activo: 'bg-green-100 text-green-800',
    inactivo: 'bg-red-100 text-red-800',
    pendiente: 'bg-yellow-100 text-yellow-800'
  }
  return classes[estado] || 'bg-gray-100 text-gray-800'
}

const getEstadoLabel = (estado) => {
  const labels = {
    activo: 'Activo',
    inactivo: 'Inactivo',
    pendiente: 'Pendiente'
  }
  return labels[estado] || estado
}

const formatFecha = (fecha) => {
  if (!fecha) return '-'
  return new Date(fecha).toLocaleDateString('es-ES')
}

const ordenarPor = (columna) => {
  if (orden.value.columna === columna) {
    orden.value.direccion = orden.value.direccion === 'asc' ? 'desc' : 'asc'
  } else {
    orden.value.columna = columna
    orden.value.direccion = 'asc'
  }
}

const toggleEstado = (item) => {
  const nuevoEstado = item.estado === 'activo' ? 'inactivo' : 'activo'
  emit('estado-cambiado', { ...item, estado: nuevoEstado })
}

const limpiarFiltros = () => {
  searchQuery.value = ''
  filters.value.estado = ''
}

const exportarDatos = () => {
  const datos = itemsFiltrados.value.map(item => {
    const fila = {}
    props.columnas.forEach(col => {
      fila[col.label] = getItemValue(item, col.key)
    })
    return fila
  })
  
  const csv = convertirACSV(datos)
  descargarCSV(csv, `${catalogoConfig.plural}_${new Date().toISOString().split('T')[0]}.csv`)
}

const convertirACSV = (datos) => {
  if (datos.length === 0) return ''
  
  const headers = Object.keys(datos[0])
  const csvRows = [
    headers.join(','),
    ...datos.map(row => 
      headers.map(header => {
        const valor = row[header] || ''
        return `"${String(valor).replace(/"/g, '""')}"`
      }).join(',')
    )
  ]
  
  return csvRows.join('\n')
}

const descargarCSV = (csv, filename) => {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.catalogo-manager {
  min-height: 500px;
}
</style>