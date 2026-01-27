<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Comunidad Autónoma -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        <MapIcon class="w-4 h-4 inline mr-1" />
        Comunidad Autónoma
      </label>
      <select
        v-model="selectedComunidad"
        @change="onComunidadChange"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        :disabled="disabled || loading"
      >
        <option value="">{{ loading ? 'Cargando...' : 'Todas las CC.AA.' }}</option>
        <option
          v-for="ccaa in comunidadesAutonomas"
          :key="ccaa.id"
          :value="ccaa.id"
        >
          {{ ccaa.nombre }}
        </option>
      </select>
    </div>

    <!-- Provincia -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        <MapPinIcon class="w-4 h-4 inline mr-1" />
        Provincia
      </label>
      <select
        v-model="selectedProvincia"
        @change="onProvinciaChange"
        :disabled="!selectedComunidad || disabled || loading"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="">{{ loading ? 'Cargando...' : 'Todas las provincias' }}</option>
        <option
          v-for="provincia in provincias"
          :key="provincia.id"
          :value="provincia.id"
        >
          {{ provincia.nombre }}
        </option>
      </select>
    </div>

    <!-- Municipio -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        <BuildingOffice2Icon class="w-4 h-4 inline mr-1" />
        Municipio
      </label>
      <select
        v-model="selectedMunicipio"
        @change="onMunicipioChange"
        :disabled="!selectedProvincia || disabled || loading"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="">{{ loading ? 'Cargando...' : 'Todos los municipios' }}</option>
        <option
          v-for="municipio in municipios"
          :key="municipio.id"
          :value="municipio.id"
        >
          {{ municipio.nombre }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { MapIcon, MapPinIcon, BuildingOffice2Icon } from '@heroicons/vue/24/outline'
import { useGeografiaStore } from '../stores/geografia'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      comunidadAutonomaId: null,
      provinciaId: null,
      municipioId: null
    })
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// Usar el store de geografía (datos cacheados en memoria)
const geografiaStore = useGeografiaStore()

// State local para selecciones
const selectedComunidad = ref(props.modelValue?.comunidadAutonomaId || '')
const selectedProvincia = ref(props.modelValue?.provinciaId || '')
const selectedMunicipio = ref(props.modelValue?.municipioId || '')

// Computed que obtienen datos del store (sin llamadas al servidor)
const comunidadesAutonomas = computed(() => geografiaStore.comunidadesAutonomas)
const provincias = computed(() => geografiaStore.getProvinciasDeCcaa(selectedComunidad.value))
const municipios = computed(() => geografiaStore.getMunicipiosDeProvincia(selectedProvincia.value))
const loading = computed(() => geografiaStore.loading)

// Cargar datos del store al montar (solo la primera vez en toda la app)
onMounted(async () => {
  await geografiaStore.cargarDatos()
})

const onComunidadChange = () => {
  // Resetear provincia y municipio (sin llamadas al servidor)
  selectedProvincia.value = ''
  selectedMunicipio.value = ''
  emitChange()
}

const onProvinciaChange = () => {
  // Resetear municipio (sin llamadas al servidor)
  selectedMunicipio.value = ''
  emitChange()
}

const onMunicipioChange = () => {
  emitChange()
}

const emitChange = () => {
  const value = {
    comunidadAutonomaId: selectedComunidad.value || null,
    provinciaId: selectedProvincia.value || null,
    municipioId: selectedMunicipio.value || null
  }

  emit('update:modelValue', value)
  emit('change', value)
}

// Watch para cambios externos en el modelValue
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    selectedComunidad.value = newValue.comunidadAutonomaId || ''
    selectedProvincia.value = newValue.provinciaId || ''
    selectedMunicipio.value = newValue.municipioId || ''
  }
}, { deep: true })
</script>
