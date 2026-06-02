<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <div class="p-4 border-b border-gray-200 flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-900">Notarías</h2>
      <button 
        @click="$emit('create')"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Nueva Notaría
      </button>
    </div>

    <div v-if="hasItems" class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <NotariaCard 
        v-for="notaria in items" 
        :key="notaria.id"
        :notaria="notaria"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>

    <div v-else-if="!loading" class="p-12 text-center">
      <ScaleIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500">No se encontraron notarías</p>
      <button 
        @click="$emit('create')"
        class="mt-4 text-blue-600 hover:text-blue-700 font-medium"
      >
        Crear la primera notaría
      </button>
    </div>

    <div v-if="loading" class="p-12 text-center">
      <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
      <p class="mt-2 text-gray-500">Cargando...</p>
    </div>

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
        <span class="px-3 py-1 bg-blue-600 text-white rounded">
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
  ScaleIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import NotariaCard from './NotariaCard.vue'

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