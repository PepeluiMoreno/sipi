<!-- InmuebleMapa.vue -->
<template>
  <div class="h-full w-full relative">
    <div ref="mapContainer" class="h-full w-full rounded-lg"></div>
    
    <!-- Info overlay -->
    <div v-if="inmuebles.length === 0" class="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-90 rounded-lg">
      <div class="text-center">
        <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
        <p class="text-gray-600">No hay inmuebles con coordenadas para mostrar</p>
      </div>
    </div>

    <!-- Contador -->
    <div v-else class="absolute top-4 right-4 bg-white px-4 py-2 rounded-lg shadow-lg border border-gray-200 z-[1000]">
      <span class="text-sm font-medium text-gray-700">{{ inmuebles.length }} inmuebles</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix para iconos de Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const props = defineProps({
  inmuebles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select'])

const mapContainer = ref(null)
let map = null
let markers = []

onMounted(() => {
  initMap()
})

// Watch para actualizar mapa cuando cambien los inmuebles (filtros aplicados)
watch(() => props.inmuebles, (newInmuebles) => {
  actualizarMarcadores(newInmuebles)
}, { deep: true })

const initMap = () => {
  if (!mapContainer.value) return

  // Crear mapa centrado en España
  map = L.map(mapContainer.value, {
    center: [40.4168, -3.7038],
    zoom: 6,
    zoomControl: true
  })

  // Tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map)

  // Cargar marcadores iniciales
  actualizarMarcadores(props.inmuebles)
}

const actualizarMarcadores = (inmuebles) => {
  if (!map) return

  // Limpiar marcadores existentes
  markers.forEach(m => map.removeLayer(m))
  markers = []

  // Filtrar solo inmuebles con coordenadas válidas
  const inmueblesConCoords = inmuebles.filter(inmueble => {
    const lat = inmueble.latitud || inmueble.lat
    const lng = inmueble.longitud || inmueble.lng
    return lat && lng && !isNaN(lat) && !isNaN(lng)
  })

  // Crear marcadores
  inmueblesConCoords.forEach(inmueble => {
    const lat = inmueble.latitud || inmueble.lat
    const lng = inmueble.longitud || inmueble.lng

    // Icono personalizado según si es BIC
    const icon = (inmueble.codigo_bien_interes_cultural || inmueble.es_bic) 
      ? L.icon({
          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        })
      : undefined

    const marker = L.marker([lat, lng], icon ? { icon } : {})
      .bindPopup(`
        <div class="text-sm min-w-[200px]">
          <strong class="block mb-1">${inmueble.denominacion_principal}</strong>
          <span class="text-gray-600 block text-xs">${inmueble.direccion || ''}</span>
          <span class="text-gray-500 block text-xs mt-1">${inmueble.localidad}, ${inmueble.provincia}</span>
          ${inmueble.codigo_bien_interes_cultural || inmueble.es_bic ? '<span class="inline-block mt-2 px-2 py-0.5 bg-amber-100 text-amber-800 text-xs font-semibold rounded">BIC</span>' : ''}
        </div>
      `)
      .on('click', () => emit('select', inmueble.id))

    marker.addTo(map)
    markers.push(marker)
  })

  // Ajustar vista si hay marcadores
  if (markers.length > 0) {
    const group = L.featureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.1))
  } else {
    // Volver a vista por defecto de España
    map.setView([40.4168, -3.7038], 6)
  }
}
</script>

<style scoped>
:deep(.leaflet-container) {
  font-family: inherit;
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
}

:deep(.leaflet-popup-content) {
  margin: 12px;
}
</style>