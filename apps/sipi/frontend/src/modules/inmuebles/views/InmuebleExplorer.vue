<!-- src/modules/inmuebles/views/InmuebleExplorer.vue -->
<template>
  <div class="inmueble-explorer-layout">
    
    <InmuebleHeader 
      :title="'Inventario de Inmuebles'"
      :subtitle="`${inmuebles.length} inmuebles encontrados`"
      :filter-stats="filterStats"
      @create-inmueble="crearInmueble"
      @open-map="abrirMapa"
    />

    <div class="main-layout">
      
      <InmuebleSidebar 
        :filters="filters"
        :is-collapsed="sidebarCollapsed"
        @filters-change="onFiltersChange"
        @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
      />

      <div class="content-main">
        
        <!-- Carrusel -->
        <div class="carousel-section">
          <InmuebleCardsContainer 
            :inmuebles="inmuebles"
            :inmueble-seleccionado="inmuebleSeleccionado"
            :layout="'horizontal'"
            :loading="loading"
            :has-filters="hasActiveFilters"
            @inmueble-seleccionado="seleccionarInmueble"
            @clear-filters="limpiarFiltros"
          />
        </div>

        <!-- Tabs como componente separado -->
        <InmuebleTabs 
          :inmueble="inmuebleSeleccionado"
          :active-tab="tabActiva"
          @tab-change="tabActiva = $event"
          @update:inmueble="actualizarInmueble"
        />

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useInmueble } from '../composables/useInmueble'

// Components
import InmuebleHeader from '../layouts/InmuebleHeader.vue'
import InmuebleSidebar from '../layouts/InmuebleSidebar.vue'
import InmuebleCardsContainer from '../components/cards/InmuebleCardsContainer.vue'
import InmuebleTabs from '@/modules/inmuebles/components/forms/tabs/InmuebleTabs.vue'

// Composable
const { 
  inmuebles: inmueblesData, 
  loading, 
  error,
  listar 
} = useInmueble()

// Estados reactivos
const inmuebleSeleccionado = ref(null)
const tabActiva = ref('basicos')
const sidebarCollapsed = ref(false)
const filters = ref({
  search: '',
  provincia: '',
  localidad: '',
  estados: []
})

// Asegurar que inmuebles siempre sea un array
const inmuebles = computed(() => {
  return inmueblesData.value || []
})

// Computed properties
const filterStats = computed(() => {
  return {
    total: inmuebles.value.length,
    filtered: inmuebles.value.length, // Puedes ajustar esto según tu lógica de filtrado
    hasActiveFilters: hasActiveFilters.value
  }
})

const hasActiveFilters = computed(() => {
  return filters.value.search || 
         filters.value.provincia || 
         filters.value.localidad || 
         filters.value.estados.length > 0
})

// Métodos
const crearInmueble = () => {
  // Lógica para crear nuevo inmueble
  console.log('Crear nuevo inmueble')
}

const abrirMapa = () => {
  // Lógica para abrir mapa
  console.log('Abrir mapa')
}

const onFiltersChange = (newFilters) => {
  filters.value = newFilters
  // Aquí puedes agregar lógica para filtrar los inmuebles
}

const seleccionarInmueble = (inmueble) => {
  inmuebleSeleccionado.value = inmueble
}

const limpiarFiltros = () => {
  filters.value = {
    search: '',
    provincia: '',
    localidad: '',
    estados: []
  }
}

const actualizarInmueble = (inmuebleActualizado) => {
  inmuebleSeleccionado.value = inmuebleActualizado
  // Aquí puedes agregar lógica para actualizar en la lista
}

// Cargar inmuebles al montar el componente
onMounted(() => {
  listar()
})
</script>

<style scoped>
.inmueble-explorer-layout {
  @apply h-screen flex flex-col bg-gray-50;
  max-height: 100vh;
  overflow: hidden;
}

.main-layout {
  @apply flex-1 flex overflow-hidden;
  min-height: 0;
}

.content-main {
  @apply flex-1 flex flex-col overflow-hidden;
}

.carousel-section {
  @apply bg-white border-b border-gray-200 flex-shrink-0;
}
</style>