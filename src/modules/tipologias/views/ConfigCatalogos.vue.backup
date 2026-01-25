<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Configuración de Catálogos</h1>
        <p class="text-gray-600">Gestione los catálogos del sistema</p>
      </div>
    </div>

    <!-- Selector de catálogo -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Seleccione un catálogo
          </label>
          <select 
            v-model="catalogoSeleccionado"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">-- Seleccione --</option>
            <option value="tipoInmueble">Tipos de Inmueble</option>
            <option value="tipoDocumento">Tipos de Documento</option>
            <option value="tipoVia">Tipos de Vía</option>
            <option value="estadoConservacion">Estados de Conservación</option>
            <option value="estadoTratamiento">Estados de Tratamiento</option>
            <option value="figuraProteccion">Figuras de Protección</option>
            <option value="fuenteDocumental">Fuentes Documentales</option>
            <option value="rolTecnico">Roles de Técnico</option>
            <option value="tipoCertificacionPropiedad">Tipos de Certificación</option>
            <option value="tipoLicencia">Tipos de Licencia</option>
            <option value="tipoMimeDocumento">Tipos MIME</option>
            <option value="tipoPersona">Tipos de Persona</option>
            <option value="tipoTransmision">Tipos de Transmisión</option>
          </select>
        </div>
        
        <div class="flex items-end">
          <button 
            @click="crearNuevo"
            :disabled="!catalogoSeleccionado"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <PlusIcon class="w-4 h-4 mr-2" />
            Nuevo Item
          </button>
        </div>
      </div>
    </div>

    <!-- DataGrid del catálogo -->
    <div v-if="catalogoSeleccionado" class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="p-4 border-b border-gray-200 flex justify-between items-center">
        <h2 class="text-lg font-semibold text-gray-900">{{ nombreCatalogo }}</h2>
      </div>

      <div v-if="loading" class="p-12 text-center">
        <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
        <p class="mt-2 text-gray-500">Cargando...</p>
      </div>

      <div v-else-if="items.length === 0" class="p-12 text-center">
        <ArchiveBoxIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <p class="text-gray-500">No hay elementos en este catálogo</p>
      </div>

      <div v-else class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div 
          v-for="item in items" 
          :key="item.id"
          class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex justify-between items-start">
            <h3 class="text-lg font-semibold text-gray-900">{{ item.nombre }}</h3>
            <div class="flex space-x-2">
              <button 
                @click="editarItem(item)"
                class="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
              >
                <PencilSquareIcon class="w-4 h-4" />
              </button>
              <button 
                @click="eliminarItem(item.id)"
                class="p-1 text-red-600 hover:bg-red-50 rounded"
              >
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <p v-if="item.descripcion" class="text-sm text-gray-600 mt-2">{{ item.descripcion }}</p>
        </div>
      </div>

      <!-- Paginación -->
      <div v-if="pagination.totalPages > 1" class="p-4 border-t border-gray-200 flex justify-between items-center">
        <div class="text-sm text-gray-600">
          Mostrando {{ items.length }} de {{ pagination.total }} resultados
        </div>
        <div class="flex space-x-2">
          <button 
            @click="cambiarPagina(pagination.page - 1)"
            :disabled="pagination.page <= 1"
            class="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
          >
            Anterior
          </button>
          <span class="px-3 py-1 bg-indigo-600 text-white rounded">
            Pág. {{ pagination.page }}
          </span>
          <button 
            @click="cambiarPagina(pagination.page + 1)"
            :disabled="pagination.page >= pagination.totalPages"
            class="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>

    <!-- Modal de formulario -->
    <CatalogoFormModal
      v-if="showModal"
      :show="showModal"
      :item="itemSeleccionado"
      :catalogo="catalogoSeleccionado"
      :loading="saving"
      @close="cerrarModal"
      @save="guardarItem"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, computed } from 'vue'
import { ArrowPathIcon, PlusIcon, ArchiveBoxIcon, PencilSquareIcon, TrashIcon } from '@heroicons/vue/24/outline'
import CatalogoFormModal from '../components/Config.vue'
// Si necesitas varios composables en el mismo archivo
import { 
  useCatalogoBase, 
  useTipoLicencia, 
  useEstadoConservacion 
} from '/src/modules/catalogos/composables'

// Estado
const catalogoSeleccionado = ref('')
const items = ref([])
const itemSeleccionado = ref(null)
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 50,
  total: 0,
  totalPages: 0
})

// Nombres legibles para los catálogos
const nombresCatalogos = {
  tipoInmueble: 'Tipos de Inmueble',
  tipoDocumento: 'Tipos de Documento',
  tipoVia: 'Tipos de Vía',
  estadoConservacion: 'Estados de Conservación',
  estadoTratamiento: 'Estados de Tratamiento',
  figuraProteccion: 'Figuras de Protección',
  fuenteDocumental: 'Fuentes Documentales',
  rolTecnico: 'Roles de Técnico',
  tipoCertificacionPropiedad: 'Tipos de Certificación',
  tipoLicencia: 'Tipos de Licencia',
  tipoMimeDocumento: 'Tipos MIME',
  tipoPersona: 'Tipos de Persona',
  tipoTransmision: 'Tipos de Transmisión'
}

const nombreCatalogo = computed(() => {
  return nombresCatalogos[catalogoSeleccionado.value] || ''
})

// Service
const catalogoService = ref(null)

// Cargar datos cuando se seleccione un catálogo
watch(catalogoSeleccionado, async (nuevoValor) => {
  if (!nuevoValor) {
    items.value = []
    return
  }
  
  // Resetear servicio y paginación
  pagination.value.page = 1
  catalogoService.value = useCatalogo(nuevoValor)
  
  await cargarItems()
})

// Funciones
const cargarItems = async () => {
  loading.value = true
  try {
    const { items: data, total } = await catalogoService.value.listar()
    items.value = data
    pagination.value.total = total
    pagination.value.totalPages = Math.ceil(total / pagination.value.pageSize)
  } catch (error) {
    console.error('Error cargando catálogo:', error)
  } finally {
    loading.value = false
  }
}

const cambiarPagina = async (page) => {
  if (page < 1 || page > pagination.value.totalPages) return
  pagination.value.page = page
  await cargarItems()
}

const crearNuevo = () => {
  itemSeleccionado.value = null
  showModal.value = true
}

const editarItem = (item) => {
  itemSeleccionado.value = item
  showModal.value = true
}

const cerrarModal = () => {
  showModal.value = false
  itemSeleccionado.value = null
}

const guardarItem = async (data) => {
  saving.value = true
  try {
    if (data.id) {
      await catalogoService.value.actualizar(data.id, data)
    } else {
      await catalogoService.value.crear(data)
    }
    await cargarItems()
    cerrarModal()
  } catch (error) {
    console.error('Error guardando item:', error)
  } finally {
    saving.value = false
  }
}

const eliminarItem = async (id) => {
  if (!confirm('¿Está seguro de eliminar este item?')) return
  
  try {
    await catalogoService.value.eliminar(id)
    await cargarItems()
  } catch (error) {
    console.error('Error eliminando item:', error)
  }
}

onMounted(() => {
  // Inicialización si es necesaria
})
</script>

<style scoped>
/* Estilos específicos si son necesarios */
</style>