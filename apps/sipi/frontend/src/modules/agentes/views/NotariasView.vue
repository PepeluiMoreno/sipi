<!-- NotariasView — estándar de agentes: FilterSidebar vertical + maestro-detalle (sin modal). -->
<template>
  <AgenteCrudShell
    titulo="Notarías"
    :total="total"
    :editando="editando"
    nuevo-label="Nueva notaría"
    @nuevo="nuevo"
  >
    <template #filtros>
      <NotariaFiltros @filter-change="handleFilterChange" />
    </template>

    <template #lista>
      <NotariaDataGrid
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
      <NotariaForm
        :notaria="selectedNotaria"
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
import { useNotaria } from '../composables/useNotaria'
import AgenteCrudShell from '../../core/components/AgenteCrudShell.vue'
import NotariaFiltros from '../components/notaria/NotariaFiltros.vue'
import NotariaDataGrid from '../components/notaria/NotariaDataGrid.vue'
import NotariaForm from '../components/notaria/NotariaForm.vue'
import EliminarConfirmModal from '../../core/components/ui/EliminarConfirmModal.vue'

const notariaService = useNotaria()
const { items, loading, hasMore } = notariaService

const total = ref(0)
const saving = ref(false)
const editando = ref(false)
const selectedNotaria = ref(null)
const filters = ref({})

const eliminarOpen = ref(false)
const eliminarId = ref(null)
const eliminarNombre = ref('')

onMounted(loadNotarias)

async function loadNotarias () {
  try {
    const r = await notariaService.listar(filters.value)
    if (r) total.value = r.total
  } catch (error) {
    console.error('Error cargando notarías:', error)
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  await loadNotarias()
}

const cargarMas = async () => {
  const r = await notariaService.cargarMas()
  if (r) total.value = r.total
}

const nuevo = () => { selectedNotaria.value = null; editando.value = true }
const editar = (id) => { selectedNotaria.value = items.value.find(n => n.id === id) || null; editando.value = true }
const cerrarForm = () => { editando.value = false; selectedNotaria.value = null }

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) await notariaService.actualizar(data.id, data)
    else await notariaService.crear(data)
    await loadNotarias()
    cerrarForm()
  } catch (error) {
    console.error('Error guardando notaría:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = (id) => {
  eliminarId.value = id
  eliminarNombre.value = items.value.find(n => n.id === id)?.nombre || ''
  eliminarOpen.value = true
}

const onConfirmEliminar = async (permanente) => {
  const id = eliminarId.value
  if (!id) return
  try {
    if (permanente) await notariaService.purgar(id)
    else await notariaService.eliminar(id)
    await loadNotarias()
  } catch (error) {
    console.error('Error eliminando notaría:', error)
  } finally {
    eliminarId.value = null
  }
}
</script>
