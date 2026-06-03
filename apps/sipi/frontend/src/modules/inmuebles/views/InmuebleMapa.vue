<!-- modules/inmuebles/views/InmuebleMapa.vue -->
<template>
  <div class="inmueble-mapa">
    <div ref="mapContainer" class="map-container"></div>
    
    <!-- Controles del mapa -->
    <div class="map-controls">
      <button @click="zoomIn" class="control-btn">
        <i class="fas fa-plus"></i>
      </button>
      <button @click="zoomOut" class="control-btn">
        <i class="fas fa-minus"></i>
      </button>
      <button @click="resetView" class="control-btn">
        <i class="fas fa-crosshairs"></i>
      </button>
    </div>

    <!-- Leyenda -->
    <div class="map-legend">
      <div class="legend-item">
        <div class="legend-color bg-green-500"></div>
        <span>Inmatriculado</span>
      </div>
      <div class="legend-item">
        <div class="legend-color bg-orange-500"></div>
        <span>Vendido</span>
      </div>
      <div class="legend-item">
        <div class="legend-color bg-yellow-500"></div>
        <span>En Venta</span>
      </div>
      <div class="legend-item">
        <div class="legend-color bg-purple-500"></div>
        <span>BIC</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'

const props = defineProps({
  inmuebles: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  zoom: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['marker-click'])

const mapContainer = ref(null)
let map = null
let markers = []

// Inicializar mapa
const initMap = () => {
  if (!mapContainer.value) return

  // En un entorno real, aquí inicializarías Leaflet u OpenLayers
  console.log('Inicializando mapa con:', props.inmuebles.length, 'inmuebles')
  
  // Simulación de marcadores
  createMarkers()
}

const createMarkers = () => {
  // Limpiar marcadores existentes
  clearMarkers()

  props.inmuebles.forEach(inmueble => {
    if (inmueble.lat && inmueble.lng) {
      const marker = {
        id: inmueble.id,
        lat: inmueble.lat,
        lng: inmueble.lng,
        estado: inmueble.estado,
        es_bic: inmueble.es_bic
      }
      markers.push(marker)
    }
  })
}

const clearMarkers = () => {
  markers = []
}

const getMarkerColor = (estado, esBic) => {
  if (esBic) return 'purple'
  
  const colors = {
    'Inmatriculado': 'green',
    'Vendido': 'orange',
    'En venta': 'yellow',
    'No investigado': 'gray'
  }
  return colors[estado] || 'blue'
}

const handleMarkerClick = (inmuebleId) => {
  emit('marker-click', inmuebleId)
}

const zoomIn = () => {
  // Lógica para zoom in
  console.log('Zoom in')
}

const zoomOut = () => {
  // Lógica para zoom out
  console.log('Zoom out')
}

const resetView = () => {
  // Lógica para resetear vista
  console.log('Reset view')
}

// Watchers
watch(() => props.inmuebles, () => {
  createMarkers()
}, { deep: true })

// Lifecycle
onMounted(() => {
  initMap()
})

onUnmounted(() => {
  clearMarkers()
})
</script>

<style scoped>
.inmueble-mapa {
  @apply relative h-full w-full;
}

.map-container {
  @apply h-full w-full bg-gray-200 rounded-lg;
  background-image: 
    linear-gradient(45deg, #f0f0f0 25%, transparent 25%), 
    linear-gradient(-45deg, #f0f0f0 25%, transparent 25%), 
    linear-gradient(45deg, transparent 75%, #f0f0f0 75%), 
    linear-gradient(-45deg, transparent 75%, #f0f0f0 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
}

.map-controls {
  @apply absolute top-4 right-4 flex flex-col space-y-2;
}

.control-btn {
  @apply w-10 h-10 bg-white rounded shadow-sm flex items-center justify-center 
         hover:bg-gray-50 transition-colors;
}

.map-legend {
  @apply absolute bottom-4 left-4 bg-white rounded shadow-sm p-3 space-y-2;
}

.legend-item {
  @apply flex items-center space-x-2 text-sm;
}

.legend-color {
  @apply w-4 h-4 rounded-full;
}
</style>