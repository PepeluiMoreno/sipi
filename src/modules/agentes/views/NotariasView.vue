<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Notarías</h1>
        <p class="text-gray-600">Gestión de notarías</p>
      </div>
    </div>

    <NotariaFiltros
      :comunidades-autonomas="comunidadesAutonomas"
      :provincias="provincias"
      :localidades="localidades"
      @filter-change="handleFilterChange"
    />

    <NotariaDataGrid 
      :items="items"
      :loading="loading"
      :pagination="pagination"
      @create="openCreateModal"
      @edit="openEditModal"
      @delete="handleDelete"
      @change-page="handlePageChange"
    />

    <NotariaFormModal
      :show="showModal"
      :notaria="selectedNotaria"
      :localidades="localidades"
      :loading="saving"
      @close="closeModal"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useNotaria } from '../composables/useNotaria'
import { useTipologiaBase } from '../../tipologias/composables/useTipologiaBase'
import NotariaFiltros from '../components/notaria/NotariaFiltros.vue'
import NotariaDataGrid from '../components/notaria/NotariaDataGrid.vue'
import NotariaFormModal from '../components/notaria/NotariaFormModal.vue'

const notariaService = useNotaria()
const localidadService = useTipologiaBase('municipios', { conContacto: false })
const ccaaService = useTipologiaBase('comunidadesAutonomas', { conContacto: false })
const provinciaService = useTipologiaBase('provincias', { conContacto: false })

const items = ref([])
const localidades = ref([])
const comunidadesAutonomas = ref([])
const provincias = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const selectedNotaria = ref(null)
const filters = ref({})

onMounted(async () => {
  await loadComunidadesAutonomas()
  await loadProvincias()
  await loadLocalidades()
  await loadNotarias()
})

const loadComunidadesAutonomas = async () => {
  try {
    const { items: ccaas } = await ccaaService.listar()
    comunidadesAutonomas.value = ccaas
  } catch (error) {
    console.error('Error cargando comunidades autónomas:', error)
  }
}

const loadProvincias = async () => {
  try {
    const { items: provs } = await provinciaService.listar()
    provincias.value = provs
  } catch (error) {
    console.error('Error cargando provincias:', error)
  }
}

const loadLocalidades = async () => {
  try {
    const { items: locs } = await localidadService.listar()
    localidades.value = locs
  } catch (error) {
    console.error('Error cargando localidades:', error)
  }
}

const loadNotarias = async () => {
  loading.value = true
  try {
    const { items: nots } = await notariaService.listar(filters.value)
    items.value = nots
  } catch (error) {
    console.error('Error cargando notarías:', error)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  notariaService.pagination.page = 1
  await loadNotarias()
}

const handlePageChange = async (newPage) => {
  notariaService.cambiarPagina(newPage)
  await loadNotarias()
}

const openCreateModal = () => {
  selectedNotaria.value = null
  showModal.value = true
}

const openEditModal = (id) => {
  selectedNotaria.value = items.value.find(n => n.id === id)
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedNotaria.value = null
}

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) {
      await notariaService.actualizar(data.id, data)
    } else {
      await notariaService.crear(data)
    }
    await loadNotarias()
    closeModal()
  } catch (error) {
    console.error('Error guardando notaría:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('¿Está seguro de eliminar esta notaría?')) return
  
  try {
    await notariaService.eliminar(id)
    await loadNotarias()
  } catch (error) {
    console.error('Error eliminando notaría:', error)
  }
}

const { pagination } = notariaService
</script>