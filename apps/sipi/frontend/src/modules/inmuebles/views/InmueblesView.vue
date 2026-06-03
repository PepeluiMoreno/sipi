<!-- InmueblesView.vue — lista de inmuebles a altura completa, sin scroll de página -->
<template>
  <div class="flex h-full min-h-0 bg-zinc-100">
    <InmueblesSidebar
      v-model:filters="filters"
      :estados="catalogos.estados"
      :tipos-inmueble="catalogos.tiposInmueble"
      :comunidades-autonomas="catalogos.comunidadesAutonomas"
      :provincias="catalogos.provincias"
      :localidades="catalogos.localidades"
      @apply="aplicarFiltros"
      @clear="limpiarFiltros"
    />

    <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
      <InmuebleToolbar
        v-model:view="vistaActiva"
        :total="filteredCount"
        @nuevo="irANuevo"
      />

      <div class="flex-1 min-h-0 overflow-auto p-4">
        <UiEmptyState v-if="loading" loading loading-text="Cargando inmuebles…" />

        <UiEmptyState
          v-else-if="isEmpty"
          icon="inmueble"
          title="No hay inmuebles"
          description="Aún no hay inmuebles que coincidan con los filtros."
        >
          <template #action>
            <UiButton variant="primary" icon="plus" @click="irANuevo">Crear inmueble</UiButton>
          </template>
        </UiEmptyState>

        <div v-else-if="vistaActiva === 'cards'"
             class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <InmuebleCard
            v-for="inmueble in inmuebles"
            :key="inmueble.id"
            :inmueble="inmueble"
            @click="irADetalle(inmueble.id)"
          />
        </div>

        <InmuebleMapa
          v-else-if="vistaActiva === 'mapa'"
          :inmuebles="inmuebles"
          @select="irADetalle"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useInmueble } from '../composables/useInmueble'
import InmueblesSidebar from '../components/InmueblesSidebar.vue'
import InmuebleToolbar from '../components/InmuebleToolbar.vue'
import InmuebleCard from '../components/InmuebleCard.vue'
import InmuebleMapa from '../components/InmuebleMapa.vue'

const router = useRouter()
const vistaActiva = ref('cards')
const filters = ref({
  search: '',
  estados: {},
  comunidadAutonoma: null,
  provincia: null,
  localidad: null,
  tipoInmueble: null
})

const catalogos = ref({
  estados: [],
  tiposInmueble: [],
  comunidadesAutonomas: [],
  provincias: [],
  localidades: []
})

const {
  inmuebles,
  loading,
  isEmpty,
  filteredCount,
  listar,
  obtenerCatalogos
} = useInmueble()

const aplicarFiltros = async () => {
  await listar(filters.value)
}

const limpiarFiltros = () => {
  filters.value = {
    search: '',
    estados: {},
    comunidadAutonoma: null,
    provincia: null,
    localidad: null,
    tipoInmueble: null
  }
  listar()
}

const irADetalle = (id) => {
  router.push(`/inmuebles/${id}`)
}

const irANuevo = () => {
  router.push('/inmuebles/nuevo')
}

onMounted(async () => {
  catalogos.value = await obtenerCatalogos()
  console.log('🔍 Catálogos cargados:', catalogos.value)
  await listar()
})
</script>