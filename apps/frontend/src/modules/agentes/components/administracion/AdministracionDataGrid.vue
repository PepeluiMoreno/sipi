<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <!-- Header con búsqueda y acciones -->
    <div class="p-4 border-b border-gray-200 flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-900">Administraciones</h2>
      <button 
        @click="$emit('create')"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Nueva Administración
      </button>
    </div>

    <!-- Grid de tarjetas -->
    <div v-if="hasItems" class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <AdministracionCard 
        v-for="administracion in items" 
        :key="administracion.id"
        :administracion="administracion"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>

    <!-- Estado vacío -->
    <div v-else-if="!loading" class="p-12 text-center">
      <BuildingOfficeIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500">No se encontraron administraciones</p>
      <button 
        @click="$emit('create')"
        class="mt-4 text-indigo-600 hover:text-indigo-700 font-medium"
      >
        Crear la primera administración
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center">
      <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
      <p class="mt-2 text-gray-500">Cargando...</p>
    </div>

    <!-- Paginación -->
    <div v-if="hasItems && pagination.totalPages > 1" 
         class="p-4 border-t border-gray-200 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        Mostrando {{ items.length }} de {{ pagination.total }} resultados
      </div>
      <div class="flex space-x-2">
        <button 
          @click="$emit('change-page', pagination.page - 1)"
          :disabled="pagination.page <= 1"
          class="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
        >
          Anterior
        </button>
        <span class="px-3 py-1 bg-indigo-600 text-white rounded">
          Pág. {{ pagination.page }}
        </span>
        <button 
          @click="$emit('change-page', pagination.page + 1)"
          :disabled="pagination.page >= pagination.totalPages"
          class="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
        >
          Siguiente
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  PlusIcon, 
  BuildingOfficeIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import AdministracionCard from './AdministracionCard.vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({})
  }
})

const hasItems = computed(() => props.items.length > 0)

defineEmits(['create', 'edit', 'delete', 'change-page'])
</script>