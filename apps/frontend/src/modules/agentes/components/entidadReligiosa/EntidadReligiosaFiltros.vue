<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
    <!-- Primera fila -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Búsqueda -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          <MagnifyingGlassIcon class="w-4 h-4 inline mr-1" />
          Búsqueda
        </label>
        <input
          v-model="filters.search"
          @input="$emit('filter-change', filters)"
          type="text"
          placeholder="Nombre, NIF..."
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <!-- Filtro Geográfico -->
      <div>
        <FiltroGeografico
          v-model="ubicacion"
          @change="onUbicacionChange"
          :comunidades-autonomas="comunidadesAutonomas"
          :provincias="provincias"
          :localidades="localidades"
        />
      </div>
    </div>

    <!-- Segunda fila -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      <!-- Tipo de Entidad -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          <BuildingLibraryIcon class="w-4 h-4 inline mr-1" />
          Tipo de Entidad
        </label>
        <select
          v-model="filters.tipoEntidadId"
          @change="$emit('filter-change', filters)"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Todos los tipos</option>
          <option
            v-for="tipo in tiposEntidad"
            :key="tipo.id"
            :value="tipo.id"
          >
            {{ tipo.nombre }}
          </option>
        </select>
      </div>

      <!-- Estado -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          <CheckCircleIcon class="w-4 h-4 inline mr-1" />
          Estado
        </label>
        <select
          v-model="filters.activa"
          @change="$emit('filter-change', filters)"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Todas</option>
          <option value="true">Activas</option>
          <option value="false">Inactivas</option>
        </select>
      </div>
    </div>

    <div class="mt-4 flex justify-end">
      <button
        @click="resetFilters"
        class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 flex items-center"
      >
        <FunnelIcon class="w-4 h-4 mr-1" />
        Limpiar filtros
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  BuildingLibraryIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'
import FiltroGeografico from '../../../core/components/FiltroGeografico.vue'

const props = defineProps({
  comunidadesAutonomas: {
    type: Array,
    default: () => []
  },
  provincias: {
    type: Array,
    default: () => []
  },
  localidades: {
    type: Array,
    default: () => []
  },
  tiposEntidad: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['filter-change'])

const filters = ref({
  search: '',
  tipoEntidadId: '',
  activa: ''
})

const ubicacion = ref({
  comunidadAutonomaId: null,
  provinciaId: null,
  localidadId: null
})

const onUbicacionChange = () => {
  emit('filter-change', { ...filters.value, ...ubicacion.value })
}

const resetFilters = () => {
  filters.value = {
    search: '',
    tipoEntidadId: '',
    activa: ''
  }
  ubicacion.value = {
    comunidadAutonomaId: null,
    provinciaId: null,
    localidadId: null
  }
  emit('filter-change', { ...filters.value, ...ubicacion.value })
}
</script>
