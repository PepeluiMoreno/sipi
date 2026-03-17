<!-- InmueblesView.vue -->
<template>
  <div class="flex h-screen bg-gray-50">
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

    <div class="flex-1 flex flex-col overflow-hidden">
      <InmuebleToolbar
        v-model:view="vistaActiva"
        :total="filteredCount"
        @nuevo="irANuevo"
      />

      <div class="flex-1 overflow-auto p-6">
        <div v-if="loading" class="flex items-center justify-center h-full">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <div v-else-if="isEmpty" class="flex flex-col items-center justify-center h-full text-gray-500">
          <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <p class="text-lg font-medium">No hay inmuebles</p>
          <button @click="irANuevo" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Crear primer inmueble
          </button>
        </div>

        <div v-else-if="vistaActiva === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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