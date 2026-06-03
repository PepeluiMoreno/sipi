<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">OpenStreetMap</h3>
        <p class="text-sm text-gray-600 mt-1">Datos de integración con OpenStreetMap</p>
      </div>
      <div class="flex items-center space-x-3">
        <button
          @click="sincronizarOSM"
          :disabled="sincronizando"
          class="btn btn-secondary btn-sm"
        >
          <ArrowPathIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': sincronizando }" />
          {{ sincronizando ? 'Sincronizando...' : 'Sincronizar' }}
        </button>
      </div>
    </div>

    <!-- Datos OSM -->
    <div v-if="osmData" class="space-y-6">
      <!-- ID y Tipo -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            OSM ID
          </label>
          <input
            v-model="osmData.osm_id"
            placeholder="Ej: 123456789"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Tipo OSM
          </label>
          <select
            v-model="osmData.osm_type"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">Seleccione tipo</option>
            <option value="node">Node</option>
            <option value="way">Way</option>
            <option value="relation">Relation</option>
          </select>
        </div>
      </div>

      <!-- Nombre en OSM -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Nombre en OSM
        </label>
        <input
          v-model="osmData.name"
          placeholder="Nombre tal como aparece en OpenStreetMap"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <!-- Etiquetas OSM -->
      <div class="border-t pt-6">
        <h4 class="text-md font-medium text-gray-900 mb-4">Etiquetas OSM</h4>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <label class="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="checkbox"
              v-model="osmData.ruins"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">Ruinas</span>
              <p class="text-xs text-gray-500">building=ruins</p>
            </div>
          </label>

          <label class="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="checkbox"
              v-model="osmData.has_polygon"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">Tiene polígono</span>
              <p class="text-xs text-gray-500">Geometría completa</p>
            </div>
          </label>

          <label class="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="checkbox"
              v-model="osmData.historic_building"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">Edificio histórico</span>
              <p class="text-xs text-gray-500">historic=building</p>
            </div>
          </label>

          <label class="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="checkbox"
              v-model="osmData.heritage"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">Patrimonio</span>
              <p class="text-xs text-gray-500">heritage=*</p>
            </div>
          </label>

          <label class="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="checkbox"
              v-model="osmData.religion_christian"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">Religión cristiana</span>
              <p class="text-xs text-gray-500">religion=christian</p>
            </div>
          </label>

          <label class="flex items-center space-x-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="checkbox"
              v-model="osmData.denomination_catholic"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div>
              <span class="text-sm font-medium text-gray-900">Confesión católica</span>
              <p class="text-xs text-gray-500">denomination=catholic</p>
            </div>
          </label>
        </div>
      </div>

      <!-- Metadatos OSM -->
      <div class="border-t pt-6">
        <h4 class="text-md font-medium text-gray-900 mb-4">Metadatos</h4>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Última sincronización
            </label>
            <input
              type="datetime-local"
              v-model="osmData.source_updated_at"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Versión OSM
            </label>
            <input
              type="number"
              v-model="osmData.version"
              placeholder="Versión del elemento OSM"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      <!-- Enlace OSM -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-blue-800">Enlace a OpenStreetMap</p>
            <p class="text-sm text-blue-600 mt-1">Ver este elemento en el mapa colaborativo</p>
          </div>
          <a
            v-if="enlaceOSM"
            :href="enlaceOSM"
            target="_blank"
            class="btn btn-secondary btn-sm"
          >
            <MapPinIcon class="w-4 h-4 mr-2" />
            Abrir en OSM
          </a>
        </div>
      </div>
    </div>

    <!-- Estado sin datos OSM -->
    <div
      v-else
      class="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg"
    >
      <MapPinIcon class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h4 class="text-lg font-medium text-gray-900 mb-2">Sin datos de OSM</h4>
      <p class="text-gray-500 mb-4">Este inmueble no está sincronizado con OpenStreetMap</p>
      <button
        @click="inicializarOSM"
        class="btn btn-primary"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Inicializar Datos OSM
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { MapPinIcon, ArrowPathIcon, PlusIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  property: {
    type: Object,
    required: true
  },
  errors: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:property'])

const sincronizando = ref(false)
const osmData = ref(props.property.osm_ext || null)

const enlaceOSM = computed(() => {
  if (!osmData.value?.osm_id || !osmData.value?.osm_type) return null
  return `https://www.openstreetmap.org/${osmData.value.osm_type}/${osmData.value.osm_id}`
})

watch(osmData, (newData) => {
  emit('update:property', {
    ...props.property,
    osm_ext: newData
  })
}, { deep: true })

const sincronizarOSM = async () => {
  sincronizando.value = true
  try {
    // Simular sincronización con OSM
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Aquí iría la lógica real de sincronización
    console.log('Sincronizando con OSM...')
    
  } catch (error) {
    console.error('Error sincronizando con OSM:', error)
  } finally {
    sincronizando.value = false
  }
}

const inicializarOSM = () => {
  osmData.value = {
    osm_id: '',
    osm_type: '',
    name: '',
    ruins: false,
    has_polygon: false,
    historic_building: false,
    heritage: false,
    religion_christian: false,
    denomination_catholic: false,
    source_updated_at: new Date().toISOString().slice(0, 16),
    version: 1
  }
}
</script>