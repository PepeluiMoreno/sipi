<!-- EntidadesReligiosasView — estándar: FilterSidebar + maestro-detalle (lista arriba, form debajo) + paginación a altura. -->
<template>
  <AgenteCrudShell
    titulo="Entidades religiosas"
    :total="total"
    :editando="editando"
    :seleccion="seleccion"
    nuevo-label="Nueva entidad"
    @nuevo="nuevo"
  >
    <template #filtros>
      <EntidadReligiosaFiltros :tipos-entidad="tiposEntidad" @filter-change="handleFilterChange" />
    </template>

    <template #lista>
      <EntidadReligiosaDataGrid
        :items="items"
        :loading="loading"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :selected-id="selectedId"
        @create="nuevo"
        @ver="ver"
        @edit="editar"
        @delete="handleDelete"
        @change-page="cambiarPagina"
        @update:page-size="onPageSize"
      />
    </template>

    <template #form>
      <EntidadReligiosaForm
        :entidad="selectedEntidad"
        :tipos-entidad="tiposEntidad"
        :loading="saving"
        :readonly="readonly"
        @cancelar="cerrarForm"
        @editar="modo = 'editar'"
        @save="handleSave"
      />
    </template>
  </AgenteCrudShell>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import { useEntidadReligiosa } from '../composables/useEntidadReligiosa'
import { LISTAR, LISTAR_TIPOS } from '../graphql/entidadReligiosaQueries'
import AgenteCrudShell from '../../core/components/AgenteCrudShell.vue'
import EntidadReligiosaFiltros from '../components/entidadReligiosa/EntidadReligiosaFiltros.vue'
import EntidadReligiosaDataGrid from '../components/entidadReligiosa/EntidadReligiosaDataGrid.vue'
import EntidadReligiosaForm from '../components/entidadReligiosa/EntidadReligiosaForm.vue'

const entidadService = useEntidadReligiosa() // solo para mutaciones (crear/actualizar/eliminar)
const { resolveClient } = useApolloClient()

const items = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(15)
const filters = ref({})
const tiposEntidad = ref([])

const saving = ref(false)
const modo = ref(null)              // null | 'nuevo' | 'ver' | 'editar'
const selectedEntidad = ref(null)

const editando = computed(() => modo.value !== null)
const seleccion = computed(() => modo.value === 'ver' || modo.value === 'editar')
const selectedId = computed(() => (seleccion.value ? selectedEntidad.value?.id ?? null : null))
const readonly = computed(() => modo.value === 'ver')
const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

onMounted(async () => {
  await loadTipos()
  await fetchPage()
})

const loadTipos = async () => {
  try {
    const { data } = await resolveClient().query({ query: LISTAR_TIPOS, fetchPolicy: 'cache-first' })
    tiposEntidad.value = data?.tiposEntidadReligiosa?.items ?? []
  } catch (e) { console.error('Error cargando tipos:', e) }
}

// Traduce el objeto de filtros del UI → filters:[FilterInput] (array→IN, escalar→EQ).
const construirFilters = (f = {}) => {
  const fl = []
  for (const [campo, valor] of Object.entries(f)) {
    if (campo === 'search') continue
    if (valor === null || valor === undefined || valor === '') continue
    if (Array.isArray(valor)) { if (valor.length) fl.push({ field: campo, operator: 'IN', values: valor.map(String) }); continue }
    fl.push({ field: campo, operator: 'EQ', value: String(valor) })
  }
  return fl
}

const fetchPage = async () => {
  loading.value = true
  try {
    const variables = { offset: (page.value - 1) * pageSize.value, limit: pageSize.value }
    if (typeof filters.value.search === 'string' && filters.value.search.trim()) variables.search = filters.value.search.trim()
    const fl = construirFilters(filters.value)
    if (fl.length) variables.filters = fl
    const { data } = await resolveClient().query({ query: LISTAR, variables, fetchPolicy: 'network-only' })
    items.value = data?.entidadesReligiosas?.items ?? []
    total.value = data?.entidadesReligiosas?.total ?? 0
  } catch (e) {
    console.error('Error cargando entidades religiosas:', e)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = async (newFilters) => {
  filters.value = newFilters
  page.value = 1
  await fetchPage()
}

const cambiarPagina = async (p) => {
  page.value = Math.min(Math.max(1, p), totalPaginas.value)
  await fetchPage()
}

const onPageSize = async (n) => {
  if (!n || n === pageSize.value) return
  pageSize.value = n
  page.value = 1
  await fetchPage()
}

// Maestro-detalle: la fila seleccionada se muestra colapsada arriba y el form debajo.
const nuevo = () => { selectedEntidad.value = null; modo.value = 'nuevo' }
const ver = (id) => { selectedEntidad.value = items.value.find(e => e.id === id) || null; modo.value = 'ver' }
const editar = (id) => { selectedEntidad.value = items.value.find(e => e.id === id) || null; modo.value = 'editar' }
const cerrarForm = () => { modo.value = null; selectedEntidad.value = null }

const handleSave = async (data) => {
  saving.value = true
  try {
    if (data.id) await entidadService.actualizar(data.id, data)
    else await entidadService.crear(data)
    await fetchPage()
    cerrarForm()
  } catch (e) {
    console.error('Error guardando entidad religiosa:', e)
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('¿Eliminar esta entidad religiosa?')) return
  try {
    await entidadService.eliminar(id)
    if (selectedEntidad.value?.id === id) cerrarForm()
    await fetchPage()
  } catch (e) {
    console.error('Error eliminando entidad religiosa:', e)
  }
}
</script>
