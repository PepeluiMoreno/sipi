<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
    <!-- Búsqueda -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-1">
        <MagnifyingGlassIcon class="w-4 h-4 inline mr-1" />
        Búsqueda
      </label>
      <input
        v-model="filters.search"
        @input="emitFilters"
        type="text"
        placeholder="Nombre, NIF..."
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
      />
    </div>

    <!-- Filtro geográfico reutilizable -->
    <FiltroGeografico
      v-model="filtrosGeograficos"
      @change="onGeografiaChange"
    />

    <!-- Ámbito -->
    <div class="mt-4">
      <label class="block text-sm font-medium text-gray-700 mb-1">
        <GlobeAltIcon class="w-4 h-4 inline mr-1" />
        Ámbito
      </label>
      <select
        v-model="filters.ambito"
        @change="emitFilters"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
      >
        <option value="">Todos los ámbitos</option>
        <option value="municipal">Municipal</option>
        <option value="provincial">Provincial</option>
        <option value="autonomico">Autonómico</option>
        <option value="estatal">Estatal</option>
      </select>
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
  GlobeAltIcon,
  FunnelIcon
} from '@heroicons/vue/24/outline'
import FiltroGeografico from '../../../core/components/FiltroGeografico.vue'

const emit = defineEmits(['filter-change'])

const filters = ref({
  search: '',
  ambito: ''
})

const filtrosGeograficos = ref({
  comunidadAutonomaId: null,
  provinciaId: null,
  municipioId: null
})

const onGeografiaChange = (geografia) => {
  filtrosGeograficos.value = geografia
  emitFilters()
}

const emitFilters = () => {
  emit('filter-change', {
    ...filters.value,
    ...filtrosGeograficos.value
  })
}

const resetFilters = () => {
  filters.value = {
    search: '',
    ambito: ''
  }
  filtrosGeograficos.value = {
    comunidadAutonomaId: null,
    provinciaId: null,
    municipioId: null
  }
  emitFilters()
}
</script>