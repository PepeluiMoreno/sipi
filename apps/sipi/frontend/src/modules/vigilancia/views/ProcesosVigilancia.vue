<!-- ProcesosVigilancia — estándar CRUD: AgenteCrudShell + composable + Filtros/DataGrid/Form (drawer). -->
<template>
  <AgenteCrudShell
    titulo="Procesos de vigilancia"
    :total="total"
    :editando="editando"
    nuevo-label="Nuevo proceso"
    drawer-key="vigilancia-drawer"
    @nuevo="nuevo"
  >
    <template #filtros>
      <ProcesoVigilanciaFiltros @filter-change="handleFilterChange" />
    </template>

    <template #lista>
      <ProcesoVigilanciaDataGrid
        :items="items" :loading="loading" :total="total" :has-more="hasMore"
        @edit="editar" @delete="handleDelete" @load-more="cargarMas"
      />
    </template>

    <template #form>
      <ProcesoVigilanciaForm
        :proceso="selected" :loading="saving"
        @cancelar="cerrarForm" @save="handleSave"
      />
    </template>
  </AgenteCrudShell>

  <EliminarConfirmModal v-model="eliminarOpen" :nombre="eliminarNombre" @confirm="onConfirmEliminar" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useProcesoVigilancia } from '../composables/useProcesoVigilancia'
import AgenteCrudShell from '../../core/components/AgenteCrudShell.vue'
import EliminarConfirmModal from '../../core/components/ui/EliminarConfirmModal.vue'
import ProcesoVigilanciaFiltros from '../components/ProcesoVigilanciaFiltros.vue'
import ProcesoVigilanciaDataGrid from '../components/ProcesoVigilanciaDataGrid.vue'
import ProcesoVigilanciaForm from '../components/ProcesoVigilanciaForm.vue'

const service = useProcesoVigilancia()
const { items, loading, hasMore } = service

const total = ref(0)
const saving = ref(false)
const editando = ref(false)
const selected = ref(null)
const filters = ref({})

const eliminarOpen = ref(false)
const eliminarId = ref(null)
const eliminarNombre = ref('')

onMounted(cargar)

async function cargar() {
  try { const r = await service.listar(filters.value); if (r) total.value = r.total }
  catch (e) { console.error('Error cargando procesos:', e) }
}

const handleFilterChange = async (f) => { filters.value = f; await cargar() }
const cargarMas = async () => { const r = await service.cargarMas(); if (r) total.value = r.total }

const nuevo = () => { selected.value = null; editando.value = true }
const editar = (id) => { selected.value = items.value.find(p => p.id === id) || null; editando.value = true }
const cerrarForm = () => { editando.value = false; selected.value = null }

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) {
      await service.actualizar(data.id, data)
    } else {
      const { id, ...rest } = data
      await service.crear(rest)
    }
    await cargar()
    cerrarForm()
  } catch (e) {
    console.error('Error guardando proceso:', e)
  } finally {
    saving.value = false
  }
}

const handleDelete = (id) => {
  eliminarId.value = id
  eliminarNombre.value = items.value.find(p => p.id === id)?.nombre || ''
  eliminarOpen.value = true
}

const onConfirmEliminar = async (permanente) => {
  const id = eliminarId.value
  if (!id) return
  try {
    if (permanente) await service.purgar(id)
    else await service.eliminar(id)
    await cargar()
  } catch (e) {
    console.error('Error eliminando proceso:', e)
  } finally {
    eliminarId.value = null
  }
}
</script>
