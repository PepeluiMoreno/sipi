<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Entidades Religiosas</h1>
        <p class="text-gray-600">Gestión de órdenes, congregaciones e institutos de vida consagrada</p>
      </div>
    </div>

    <EntidadReligiosaFiltros
      :comunidades-autonomas="comunidadesAutonomas"
      :provincias="provincias"
      :localidades="localidades"
      :tipos-entidad="tiposEntidad"
      @filter-change="handleFilterChange"
    />

    <EntidadReligiosaDataGrid
      :items="items"
      :loading="loading"
      :pagination="pagination"
      @create="openCreateModal"
      @edit="openEditModal"
      @delete="handleDelete"
      @change-page="handlePageChange"
    />

    <EntidadReligiosaFormModal
      :show="showModal"
      :entidad="selectedEntidad"
      :localidades="localidades"
      :tipos-entidad="tiposEntidad"
      :loading="saving"
      @close="closeModal"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEntidadReligiosa } from '../composables/useEntidadReligiosa'
import { useTipologiaBase } from '../../tipologias/composables/useTipologiaBase'
import EntidadReligiosaFiltros from '../components/entidadReligiosa/EntidadReligiosaFiltros.vue'
import EntidadReligiosaDataGrid from '../components/entidadReligiosa/EntidadReligiosaDataGrid.vue'
import EntidadReligiosaFormModal from '../components/entidadReligiosa/EntidadReligiosaFormModal.vue'

const entidadService = useEntidadReligiosa()
const localidadService = useTipologiaBase('municipios', { conContacto: false })
const ccaaService = useTipologiaBase('comunidadesAutonomas', { conContacto: false })
const provinciaService = useTipologiaBase('provincias', { conContacto: false })
const tipoEntidadService = useTipologiaBase('tiposEntidadReligiosa', { conContacto: false })

const items = ref([])
const localidades = ref([])
const comunidadesAutonomas = ref([])
const provincias = ref([])
const tiposEntidad = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const selectedEntidad = ref(null)
const filters = ref({})

onMounted(async () => {
  await loadComunidadesAutonomas()
  await loadProvincias()
  await loadLocalidades()
  await loadTiposEntidad()
  await loadEntidades()
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

const loadTiposEntidad = async () => {
  try {
    const { items: tipos } = await tipoEntidadService.listar()
    tiposEntidad.value = tipos
  } catch (error) {
    console.error('Error cargando tipos de entidad:', error)
  }
}

const loadEntidades = async () => {
  loading.value = true
  try {
    const { items: ents } = await entidadService.listar(filters.value)
    items.value = ents
  } catch (error) {
    console.error('Error cargando entidades religiosas:', error)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  entidadService.pagination.page = 1
  await loadEntidades()
}

const handlePageChange = async (newPage) => {
  entidadService.cambiarPagina(newPage)
  await loadEntidades()
}

const openCreateModal = () => {
  selectedEntidad.value = null
  showModal.value = true
}

const openEditModal = (id) => {
  selectedEntidad.value = items.value.find(e => e.id === id)
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedEntidad.value = null
}

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) {
      await entidadService.actualizar(data.id, data)
    } else {
      await entidadService.crear(data)
    }
    await loadEntidades()
    closeModal()
  } catch (error) {
    console.error('Error guardando entidad religiosa:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('¿Está seguro de eliminar esta entidad religiosa?')) return

  try {
    await entidadService.eliminar(id)
    await loadEntidades()
  } catch (error) {
    console.error('Error eliminando entidad religiosa:', error)
  }
}

const { pagination } = entidadService
</script>
