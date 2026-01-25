<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Administraciones</h1>
        <p class="text-gray-600">Gestión de administraciones patrimoniales</p>
      </div>
    </div>

    <AdministracionFiltros
      @filter-change="handleFilterChange"
    />

    <AdministracionDataGrid
      :items="items"
      :loading="loading"
      :pagination="pagination"
      @create="openCreateModal"
      @edit="openEditModal"
      @delete="handleDelete"
      @change-page="handlePageChange"
    />

    <AdministracionFormModal
      :show="showModal"
      :administracion="selectedAdministracion"
      :loading="saving"
      @close="closeModal"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdministracion } from '../composables/useAdministracion'
import AdministracionFiltros from '../components/administracion/AdministracionFiltros.vue'
import AdministracionDataGrid from '../components/administracion/AdministracionDataGrid.vue'
import AdministracionFormModal from '../components/administracion/AdministracionFormModal.vue'

const administracionService = useAdministracion()

const items = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const selectedAdministracion = ref(null)
const filters = ref({})
const pagination = administracionService.pagination

onMounted(async () => {
  await loadAdministraciones()
})

const loadAdministraciones = async () => {
  loading.value = true
  try {
    const { items: adms } = await administracionService.listar(filters.value)
    items.value = adms
  } catch (error) {
    console.error('Error cargando administraciones:', error)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  pagination.value.page = 1
  await loadAdministraciones()
}

const handlePageChange = async (newPage) => {
  administracionService.cambiarPagina(newPage)
  await loadAdministraciones()
}

const openCreateModal = () => {
  selectedAdministracion.value = null
  showModal.value = true
}

const openEditModal = (id) => {
  selectedAdministracion.value = items.value.find(a => a.id === id)
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedAdministracion.value = null
}

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) {
      await administracionService.actualizar(data.id, data)
    } else {
      await administracionService.crear(data)
    }
    await loadAdministraciones()
    closeModal()
  } catch (error) {
    console.error('Error guardando administración:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('¿Está seguro de eliminar esta administración?')) return
  
  try {
    await administracionService.eliminar(id)
    await loadAdministraciones()
  } catch (error) {
    console.error('Error eliminando administración:', error)
  }
}
</script>