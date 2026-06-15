<!-- RegistrosPropiedadView — estándar de agentes: FilterSidebar vertical + maestro-detalle (sin modal). -->
<template>
  <AgenteCrudShell
    titulo="Registros de propiedad"
    :total="total"
    :editando="editando"
    nuevo-label="Nuevo registro"
    @nuevo="nuevo"
  >
    <template #filtros>
      <RegistroPropiedadFiltros @filter-change="handleFilterChange" />
    </template>

    <template #lista>
      <RegistroPropiedadDataGrid
        :items="items"
        :loading="loading"
        :has-more="registroService.hasMore.value"
        @create="nuevo"
        @edit="editar"
        @delete="handleDelete"
        @load-more="handleLoadMore"
      />
    </template>

    <template #form>
      <RegistroPropiedadForm
        :registro="selectedRegistro"
        :loading="saving"
        @cancelar="cerrarForm"
        @save="handleSave"
      />
    </template>
  </AgenteCrudShell>

  <EliminarConfirmModal v-model="eliminarOpen" :nombre="eliminarNombre" @confirm="onConfirmEliminar" />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRegistroPropiedad } from '../composables/useRegistroPropiedad'
import { useGeografiaStore } from '@/stores/geografia'
import AgenteCrudShell from '../../core/components/AgenteCrudShell.vue'
import RegistroPropiedadFiltros from '../components/registroPropiedad/RegistroPropiedadFiltros.vue'
import RegistroPropiedadDataGrid from '../components/registroPropiedad/RegistroPropiedadDataGrid.vue'
import RegistroPropiedadForm from '../components/registroPropiedad/RegistroPropiedadForm.vue'
import EliminarConfirmModal from '../../core/components/ui/EliminarConfirmModal.vue'

const registroService = useRegistroPropiedad()
const geografiaStore = useGeografiaStore()

const { items, loading: registrosLoading } = registroService
const loading = computed(() => registrosLoading.value)

const saving = ref(false)
const editando = ref(false)
const selectedRegistro = ref(null)
const filters = ref({})
const total = ref(0)

const eliminarOpen = ref(false)
const eliminarId = ref(null)
const eliminarNombre = ref('')

onMounted(async () => {
  await geografiaStore.cargarDatos()
  await loadRegistros()
})

async function loadRegistros () {
  try {
    // El objeto de filtros estándar (search + ids) lo traduce useAgenteBase a FilterInput.
    const r = await registroService.listar(filters.value)
    if (r) total.value = r.total
  } catch (error) {
    console.error('Error cargando registros:', error)
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  await loadRegistros()
}

const handleLoadMore = async () => {
  const r = await registroService.cargarMas()
  if (r) total.value = r.total
}

const nuevo = () => { selectedRegistro.value = null; editando.value = true }
const editar = (id) => { selectedRegistro.value = items.value.find(r => r.id === id) || null; editando.value = true }
const cerrarForm = () => { editando.value = false; selectedRegistro.value = null }

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) await registroService.actualizar(data.id, data)
    else await registroService.crear(data)
    await loadRegistros()
    cerrarForm()
  } catch (error) {
    console.error('Error guardando registro:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = (id) => {
  eliminarId.value = id
  eliminarNombre.value = items.value.find(r => r.id === id)?.nombre || ''
  eliminarOpen.value = true
}

const onConfirmEliminar = async (permanente) => {
  const id = eliminarId.value
  if (!id) return
  try {
    if (permanente) await registroService.purgar(id)
    else await registroService.eliminar(id)
    await loadRegistros()
  } catch (error) {
    console.error('Error eliminando registro:', error)
  } finally {
    eliminarId.value = null
  }
}
</script>
