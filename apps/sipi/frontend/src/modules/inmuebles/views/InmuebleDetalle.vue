<!-- modules/inmuebles/views/InmuebleDetalle.vue -->
<template>
  <div class="inmueble-detalle">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin fa-2x"></i>
      <p>Cargando información del inmueble...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle fa-2x"></i>
      <h3>Error al cargar el inmueble</h3>
      <p>{{ error }}</p>
      <button @click="cargarInmueble" class="btn btn-primary">
        Reintentar
      </button>
    </div>

    <!-- Contenido -->
    <div v-else-if="inmueble" class="detalle-content">
      <!-- Header -->
      <div class="detalle-header">
        <div class="header-main">
          <button @click="$router.push('/inmuebles')" class="back-btn">
            <i class="fas fa-arrow-left"></i>
            Volver al listado
          </button>
          <h1 class="inmueble-titulo">{{ inmueble.nombre }}</h1>
          <p class="inmueble-subtitulo">{{ inmueble.direccion_normalizada }}</p>
        </div>
        <div class="header-actions">
          <button @click="editarInmueble" class="btn btn-outline">
            <i class="fas fa-edit"></i>
            Editar
          </button>
          <button @click="irATratamiento" class="btn btn-primary">
            <i class="fas fa-hard-hat"></i>
            Tratamiento
          </button>
        </div>
      </div>

      <!-- Badges de estado -->
      <div class="estado-badges">
        <span class="badge" :class="getEstadoClass(inmueble.estado)">
          {{ getEstadoLabel(inmueble.estado) }}
        </span>
        <span v-if="inmueble.es_bic" class="badge bic">
          BIC - Bien de Interés Cultural
        </span>
        <span v-if="inmueble.tieneCoordenadas" class="badge coordenadas">
          <i class="fas fa-map-marker-alt"></i>
          Geocodificado
        </span>
      </div>

      <!-- Grid principal -->
      <div class="detalle-grid">
        <!-- Columna izquierda - Información principal -->
        <div class="columna-principal">
          <!-- Imagen -->
          <div class="imagen-section">
            <img 
              :src="inmueble.photo || '/placeholder-church.jpg'" 
              :alt="inmueble.nombre"
              class="imagen-principal"
            />
          </div>

          <!-- Información básica -->
          <div class="info-card">
            <h3 class="card-titulo">
              <i class="fas fa-info-circle"></i>
              Información General
            </h3>
            <div class="info-grid">
              <div class="info-item">
                <label>Tipo de Inmueble:</label>
                <span>{{ inmueble.tipoInmueble?.nombre || 'No especificado' }}</span>
              </div>
              <div class="info-item">
                <label>Localidad:</label>
                <span>{{ inmueble.localidad?.nombre }}, {{ inmueble.provincia?.nombre }}</span>
              </div>
              <div class="info-item">
                <label>Comunidad Autónoma:</label>
                <span>{{ inmueble.comunidadAutonoma?.nombre }}</span>
              </div>
              <div class="info-item">
                <label>Diócesis:</label>
                <span>{{ inmueble.diocesis?.nombre || 'No especificada' }}</span>
              </div>
              <div class="info-item">
                <label>Estado Conservación:</label>
                <span>{{ inmueble.estadoConservacion || 'No especificado' }}</span>
              </div>
              <div class="info-item">
                <label>Inmatriculado:</label>
                <span>{{ inmueble.estaInmatriculado ? 'Sí' : 'No' }}</span>
              </div>
            </div>
          </div>

          <!-- Descripción -->
          <div v-if="inmueble.descripcion" class="info-card">
            <h3 class="card-titulo">
              <i class="fas fa-align-left"></i>
              Descripción
            </h3>
            <p class="descripcion">{{ inmueble.descripcion }}</p>
          </div>

          <!-- Mapa -->
          <div class="info-card">
            <h3 class="card-titulo">
              <i class="fas fa-map"></i>
              Ubicación
            </h3>
            <InmuebleMapa 
              :inmuebles="[inmueble]"
              :zoom="15"
              class="mini-mapa"
            />
          </div>
        </div>

        <!-- Columna derecha - Paneles de relaciones -->
        <div class="columna-secundaria">
          <!-- Denominaciones -->
          <DenominacionesPanel 
            :inmueble-id="inmuebleId"
          />

          <!-- Figuras de Protección -->
          <ProteccionPanel 
            :inmueble-id="inmuebleId"
          />

          <!-- Actuaciones -->
          <ActuacionesPanel 
            :inmueble-id="inmuebleId"
          />

          <!-- Transmisiones -->
          <TransmisionesPanel 
            :inmueble-id="inmuebleId"
          />

          <!-- Documentos -->
          <DocumentosPanel 
            :inmueble-id="inmuebleId"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInmuebleCompleto } from '../composables'
import InmuebleMapa from './InmuebleMapa.vue'
import DenominacionesPanel from '../components/DenominacionesPanel.vue'
import ProteccionPanel from '../components/ProteccionPanel.vue'
import ActuacionesPanel from '../components/ActuacionesPanel.vue'
import TransmisionesPanel from '../components/TransmisionesPanel.vue'
import DocumentosPanel from '../components/DocumentosPanel.vue'

const route = useRoute()
const router = useRouter()
const inmuebleId = route.params.id

// Composable completo para cargar todos los datos
const {
  inmueble,
  loading,
  error,
  cargarCompleto
} = useInmuebleCompleto(inmuebleId)

// Métodos
const getEstadoClass = (estado) => {
  const classes = {
    'Inmatriculado': 'estado-inmatriculado',
    'Vendido': 'estado-vendido',
    'En venta': 'estado-en-venta',
    'BIC': 'estado-bic',
    'No investigado': 'estado-no-investigado'
  }
  return classes[estado] || 'estado-default'
}

const getEstadoLabel = (estado) => {
  const labels = {
    'Inmatriculado': 'Inmatriculado',
    'Vendido': 'Vendido',
    'En venta': 'En Venta',
    'BIC': 'BIC',
    'No investigado': 'No Investigado'
  }
  return labels[estado] || estado
}

const editarInmueble = () => {
  router.push(`/inmuebles/${inmuebleId}/editar`)
}

const irATratamiento = () => {
  router.push(`/inmuebles/${inmuebleId}/tratamiento`)
}

const cargarInmueble = () => {
  cargarCompleto()
}

// Lifecycle
onMounted(() => {
  cargarCompleto()
})
</script>

<style scoped>
.inmueble-detalle {
  @apply min-h-screen bg-gray-50 p-6;
}

.loading-state, .error-state {
  @apply flex flex-col items-center justify-center py-20;
}

.detalle-content {
  @apply space-y-6;
}

.detalle-header {
  @apply flex justify-between items-start mb-6;
}

.header-main {
  @apply space-y-2;
}

.back-btn {
  @apply flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4;
}

.inmueble-titulo {
  @apply text-3xl font-bold text-gray-900;
}

.inmueble-subtitulo {
  @apply text-lg text-gray-600;
}

.estado-badges {
  @apply flex flex-wrap gap-2 mb-6;
}

.badge {
  @apply px-3 py-1 rounded-full text-sm font-semibold;
}

.estado-inmatriculado { @apply bg-green-100 text-green-800; }
.estado-vendido { @apply bg-orange-100 text-orange-800; }
.estado-en-venta { @apply bg-yellow-100 text-yellow-800; }
.estado-bic { @apply bg-purple-100 text-purple-800; }
.estado-no-investigado { @apply bg-gray-100 text-gray-800; }
.bic { @apply bg-purple-100 text-purple-800; }
.coordenadas { @apply bg-blue-100 text-blue-800; }

.detalle-grid {
  @apply grid grid-cols-1 lg:grid-cols-3 gap-6;
}

.columna-principal {
  @apply lg:col-span-2 space-y-6;
}

.columna-secundaria {
  @apply space-y-6;
}

.imagen-section {
  @apply rounded-lg overflow-hidden shadow-sm;
}

.imagen-principal {
  @apply w-full h-64 object-cover;
}

.info-card {
  @apply bg-white rounded-lg shadow-sm p-6;
}

.card-titulo {
  @apply text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2;
}

.info-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.info-item {
  @apply flex flex-col space-y-1;
}

.info-item label {
  @apply text-sm font-medium text-gray-700;
}

.info-item span {
  @apply text-gray-900;
}

.descripcion {
  @apply text-gray-700 leading-relaxed;
}

.mini-mapa {
  @apply h-64 rounded-lg overflow-hidden;
}
</style>