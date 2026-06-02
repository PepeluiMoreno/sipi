<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Registros de Propiedad</h1>
        <p class="text-gray-600">Gestión de registros de la propiedad</p>
      </div>
    </div>

    <RegistroPropiedadFiltros
      @filter-change="handleFilterChange"
    />

    <RegistroPropiedadDataGrid
      :items="items"
      :loading="loading"
      :has-more="registroService.hasMore.value"
      @create="openCreateModal"
      @edit="openEditModal"
      @delete="handleDelete"
      @load-more="handleLoadMore"
    />

    <RegistroPropiedadFormModal
      :show="showModal"
      :registro="selectedRegistro"
      :municipios="municipios"
      :loading="saving"
      @close="closeModal"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRegistroPropiedad } from '../composables/useRegistroPropiedad'
import { useGeografiaStore } from '../../core/stores/geografia'
import RegistroPropiedadFiltros from '../components/registroPropiedad/RegistroPropiedadFiltros.vue'
import RegistroPropiedadDataGrid from '../components/registroPropiedad/RegistroPropiedadDataGrid.vue'
import RegistroPropiedadFormModal from '../components/registroPropiedad/RegistroPropiedadFormModal.vue'

const registroService = useRegistroPropiedad()
const geografiaStore = useGeografiaStore()

// Usar estado del composable
const { items, loading: registrosLoading } = registroService

// Municipios desde el store (para el modal de formulario)
const municipios = computed(() => geografiaStore.municipios)

const saving = ref(false)
const showModal = ref(false)
const selectedRegistro = ref(null)
const currentFilters = ref({})

// Computed para loading
const loading = computed(() => registrosLoading.value)

onMounted(async () => {
  // Cargar datos geográficos (solo una vez, cacheados en el store)
  await geografiaStore.cargarDatos()
  await loadRegistros()
})

const loadRegistros = async () => {
  try {
    await registroService.listar(currentFilters.value)
  } catch (error) {
    console.error('Error cargando registros:', error)
  }
}

/**
 * Transforma los filtros de la UI al formato Strawchemy
 * Usa datos cacheados del store (sin llamadas al servidor)
 */
const buildStrawchemyFilter = (uiFilters) => {
  const strawchemyFilter = {}

  // Filtro de búsqueda por texto
  if (uiFilters.search && uiFilters.search.trim()) {
    const searchPattern = `%${uiFilters.search.trim()}%`
    strawchemyFilter._or = [
      { nombre: { ilike: searchPattern } },
      { nombreRegistrador: { ilike: searchPattern } },
      { direccion: { ilike: searchPattern } }
    ]
  }

  // Filtro geográfico jerárquico (usando datos del store, sin API calls)
  if (uiFilters.municipioId) {
    // Caso más específico: filtrar directamente por municipio
    strawchemyFilter.municipioId = { eq: uiFilters.municipioId }
  } else if (uiFilters.provinciaId) {
    // Filtrar por provincia: obtener IDs de municipios desde el store
    const municipioIds = geografiaStore.getMunicipioIdsDeProvincia(uiFilters.provinciaId)
    if (municipioIds.length > 0) {
      strawchemyFilter.municipioId = { in: municipioIds }
    }
  } else if (uiFilters.comunidadAutonomaId) {
    // Filtrar por CCAA: obtener IDs de municipios desde el store
    const municipioIds = geografiaStore.getMunicipioIdsDeCcaa(uiFilters.comunidadAutonomaId)
    if (municipioIds.length > 0) {
      strawchemyFilter.municipioId = { in: municipioIds }
    }
  }

  return strawchemyFilter
}

const handleFilterChange = async (newFilters) => {
  // Ya no es async - usa datos del store en memoria
  currentFilters.value = buildStrawchemyFilter(newFilters)
  await loadRegistros()
}

const handleLoadMore = async () => {
  await registroService.cargarMas()
}

const openCreateModal = () => {
  selectedRegistro.value = null
  showModal.value = true
}

const openEditModal = (id) => {
  selectedRegistro.value = items.value.find(r => r.id === id)
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedRegistro.value = null
}

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) {
      await registroService.actualizar(data.id, data)
    } else {
      await registroService.crear(data)
    }
    await loadRegistros()
    closeModal()
  } catch (error) {
    console.error('Error guardando registro:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('¿Está seguro de eliminar este registro?')) return

  try {
    await registroService.eliminar(id)
    await loadRegistros()
  } catch (error) {
    console.error('Error eliminando registro:', error)
  }
}
</script>