<template>
  <div class="inmueble-dashboard">
    <InmuebleHeader>
      <InmuebleToolbar
        :view-mode="vistaActiva"
        @view-change="cambiarVista"
        @create="mostrarModalCreacion = true"
        @refresh="recargarDatos"
      />
    </InmuebleHeader>

    <div class="dashboard-content">
      <aside class="sidebar">
        <InmuebleFiltros 
          :filters="filtersState"
          :loading="loading"
          @filters-change="onFiltersChange"
          @apply-filters="aplicarFiltros"
        />
      </aside>

      <main class="main-content">
        <div v-if="!filtrosAplicados" class="empty-state">
          <div class="empty-content">
            <i class="fas fa-search fa-3x"></i>
            <h3>Seleccione los inmuebles que quiere consultar</h3>
            <p>Utilice los filtros de la izquierda para buscar inmuebles</p>
          </div>
        </div>

        <div v-else-if="loading" class="loading-state">
          <div class="loading-content">
            <i class="fas fa-spinner fa-spin fa-2x"></i>
            <p>Cargando inmuebles...</p>
          </div>
        </div>

        <div v-else-if="inmuebles.length === 0" class="empty-state">
          <div class="empty-content">
            <i class="fas fa-home fa-3x"></i>
            <h3>No se encontraron inmuebles</h3>
            <p>Intente ajustar los criterios de búsqueda</p>
          </div>
        </div>

        <div v-else class="content-area">
          <div v-if="vistaActiva === 'grid'" class="grid-view">
            <div class="results-header">
              <span class="results-count">
                {{ inmuebles.length }} inmuebles encontrados
              </span>
            </div>
            
            <div class="cards-grid">
              <InmuebleCardGrid
                v-for="inmueble in inmuebles"
                :key="inmueble.id"
                :inmueble="inmueble"
                @click="seleccionarInmueble(inmueble)"
              />
            </div>
          </div>

          <div v-else-if="vistaActiva === 'mapa'" class="mapa-view">
            <InmuebleMapa 
              :inmuebles="inmuebles"
              @marker-click="seleccionarInmueble"
            />
          </div>
        </div>
      </main>
    </div>

    <ModalInmueble
      v-if="mostrarModalCreacion"
      @close="mostrarModalCreacion = false"
      @saved="onInmuebleGuardado"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useInmueble } from '../composables/useInmueble.js'

import InmuebleHeader from '../components/layout/InmuebleHeader.vue'
import InmuebleToolbar from '../components/ui/InmuebleToolbar.vue'
import InmuebleFiltros from '../components/filters/InmuebleFiltros.vue'
import InmuebleCardGrid from '../components/cards/InmuebleCardGrid.vue'
import InmuebleMapa from '../components/mapa/InmuebleMapa.vue'
import ModalInmueble from '../components/modals/ModalInmueble.vue'

const { inmuebles, loading, listar } = useInmueble()

const vistaActiva = ref('grid')
const mostrarModalCreacion = ref(false)
const filtrosAplicados = ref(false)
const inmueblesSeleccionados = ref([])

const filtersState = reactive({
  search: '',
  provinciaId: null,
  municipioId: null,
  estados: {
    no_investigado: false,
    inmatriculado: false,
    vendido: false,
    en_venta: false,
    bic: false
  }
})

const onFiltersChange = (nuevosFiltros) => {
  Object.assign(filtersState, nuevosFiltros)
}

const aplicarFiltros = async () => {
  filtrosAplicados.value = true
  await listar(filtersState)
}

const cambiarVista = (vista) => {
  vistaActiva.value = vista
}

const seleccionarInmueble = (inmueble) => {
  const index = inmueblesSeleccionados.value.findIndex(i => i.id === inmueble.id)
  if (index > -1) {
    inmueblesSeleccionados.value.splice(index, 1)
  } else {
    inmueblesSeleccionados.value.push(inmueble)
  }
}

const recargarDatos = async () => {
  if (filtrosAplicados.value) {
    await listar(filtersState)
  }
}

const onInmuebleGuardado = () => {
  mostrarModalCreacion.value = false
  recargarDatos()
}

onMounted(() => {
  // No cargar datos inicialmente
})
</script>

<style scoped>
.inmueble-dashboard {
  height: 100vh;
  background-color: #f9fafb;
  display: flex;
  flex-direction: column;
}

.dashboard-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 20rem;
  background: white;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
}

.main-content {
  flex: 1;
  overflow: auto;
}

.empty-state, .loading-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content, .loading-content {
  text-align: center;
  color: #6b7280;
}

.empty-content i, .loading-content i {
  margin-bottom: 1rem;
  color: #9ca3af;
}

.empty-content h3, .loading-content p {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.content-area {
  height: 100%;
  padding: 1.5rem;
}

.grid-view {
  height: 100%;
}

.results-header {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.results-count {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 1.5rem;
}

@media (min-width: 768px) {
  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .cards-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1280px) {
  .cards-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.mapa-view {
  height: 100%;
}
</style>