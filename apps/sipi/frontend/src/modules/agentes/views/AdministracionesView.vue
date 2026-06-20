<!-- AdministracionesView — estándar de agentes: FilterSidebar vertical + maestro-detalle (sin modal). -->
<template>
  <AgenteCrudShell
    titulo="Administraciones"
    :total="total"
    :editando="editando"
    nuevo-label="Nueva administración"
    @nuevo="nuevo"
  >
    <template #filtros>
      <AdministracionFiltros @filter-change="handleFilterChange" />
    </template>

    <template #lista>
      <AdministracionDataGrid
        :items="items"
        :loading="loading"
        :total="total"
        :has-more="hasMore"
        @create="nuevo"
        @edit="editar"
        @delete="handleDelete"
        @load-more="cargarMas"
      />
    </template>

    <template #form>
      <AdministracionForm
        :administracion="selectedAdministracion"
        :loading="saving"
        @cancelar="cerrarForm"
        @save="handleSave"
      />
    </template>
  </AgenteCrudShell>

  <EliminarConfirmModal v-model="eliminarOpen" :nombre="eliminarNombre" @confirm="onConfirmEliminar" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdministracion } from '../composables/useAdministracion'
import AgenteCrudShell from '../../core/components/AgenteCrudShell.vue'
import AdministracionFiltros from '../components/administracion/AdministracionFiltros.vue'
import AdministracionDataGrid from '../components/administracion/AdministracionDataGrid.vue'
import AdministracionForm from '../components/administracion/AdministracionForm.vue'
import EliminarConfirmModal from '../../core/components/ui/EliminarConfirmModal.vue'

const administracionService = useAdministracion()
const { items, loading, hasMore } = administracionService

const total = ref(0)
const saving = ref(false)
const editando = ref(false)
const selectedAdministracion = ref(null)
const filters = ref({})

const eliminarOpen = ref(false)
const eliminarId = ref(null)
const eliminarNombre = ref('')

onMounted(loadAdministraciones)

async function loadAdministraciones () {
  try {
    const r = await administracionService.listar(filters.value)
    if (r) total.value = r.total
  } catch (error) {
    console.error('Error cargando administraciones:', error)
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  await loadAdministraciones()
}

const cargarMas = async () => {
  const r = await administracionService.cargarMas()
  if (r) total.value = r.total
}

const nuevo = () => { selectedAdministracion.value = null; editando.value = true }
const editar = (id) => { selectedAdministracion.value = items.value.find(a => a.id === id) || null; editando.value = true }
const cerrarForm = () => { editando.value = false; selectedAdministracion.value = null }

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) await administracionService.actualizar(data.id, data)
    else await administracionService.crear(data)
    await loadAdministraciones()
    cerrarForm()
  } catch (error) {
    console.error('Error guardando administración:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = (id) => {
  eliminarId.value = id
  eliminarNombre.value = items.value.find(a => a.id === id)?.nombre || ''
  eliminarOpen.value = true
}

const onConfirmEliminar = async (permanente) => {
  const id = eliminarId.value
  if (!id) return
  try {
    if (permanente) await administracionService.purgar(id)
    else await administracionService.eliminar(id)
    await loadAdministraciones()
  } catch (error) {
    console.error('Error eliminando administración:', error)
  } finally {
    eliminarId.value = null
  }
}
</script>
