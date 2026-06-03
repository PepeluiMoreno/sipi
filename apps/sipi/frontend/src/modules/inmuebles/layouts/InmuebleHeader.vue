<template>
  <header class="bg-white border-b border-gray-200 px-6 py-4">
    <div class="flex items-center justify-between">
      <!-- Título y subtítulo -->
      <div class="flex-1 min-w-0">
        <h1 class="text-2xl font-bold text-gray-900 truncate">{{ title }}</h1>
        <p v-if="subtitle" class="text-sm text-gray-600 mt-1">{{ subtitle }}</p>
      </div>

      <!-- Controles del header -->
      <div class="flex items-center space-x-4">
        <!-- Selector de vista -->
        <div v-if="showViewSelector" class="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            @click="$emit('view-change', 'grid')"
            :class="[
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
              viewMode === 'grid' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Grid
          </button>
          <button
            @click="$emit('view-change', 'mapa')"
            :class="[
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
              viewMode === 'mapa' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Mapa
          </button>
        </div>

        <!-- Botón de mapa -->
        <button
          v-if="showMapButton"
          @click="$emit('open-map')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Ver Mapa
        </button>

        <!-- Botón crear inmueble -->
        <button
          @click="$emit('create-inmueble')"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Nuevo Inmueble
        </button>
      </div>
    </div>

    <!-- Información de filtros -->
    <div v-if="filterStats.hasActiveFilters" class="mt-3 flex items-center space-x-4 text-sm">
      <span class="text-gray-600">
        {{ filterStats.filtered }} de {{ filterStats.total }} inmuebles
      </span>
      <span class="text-blue-600 font-medium">Filtros aplicados</span>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'Inventario de Inmuebles'
  },
  subtitle: {
    type: String,
    default: ''
  },
  viewMode: {
    type: String,
    default: 'grid'
  },
  filterStats: {
    type: Object,
    default: () => ({
      total: 0,
      filtered: 0,
      hasActiveFilters: false
    })
  },
  selectedInmueble: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  showViewSelector: {
    type: Boolean,
    default: true
  },
  showMapButton: {
    type: Boolean,
    default: true
  }
})

defineEmits(['view-change', 'create-inmueble', 'open-map'])
</script>