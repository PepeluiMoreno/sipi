<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <div class="p-4 border-b border-gray-200 flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-900">Registros de Propiedad</h2>
      <button 
        @click="$emit('create')"
        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Nuevo Registro
      </button>
    </div>

    <div v-if="hasItems" class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <RegistroPropiedadCard 
        v-for="registro in items" 
        :key="registro.id"
        :registro="registro"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>

    <div v-else-if="!loading" class="p-12 text-center">
      <DocumentDuplicateIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500">No se encontraron registros</p>
      <button 
        @click="$emit('create')"
        class="mt-4 text-green-600 hover:text-green-700 font-medium"
      >
        Crear el primer registro
      </button>
    </div>

    <div v-if="loading" class="p-12 text-center">
      <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
      <p class="mt-2 text-gray-500">Cargando...</p>
    </div>

    <div v-if="hasItems"
         class="p-4 border-t border-gray-200 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        Mostrando {{ items.length }} registros
      </div>
      <button
        v-if="hasMore"
        @click="$emit('load-more')"
        :disabled="loading"
        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center"
      >
        <ArrowPathIcon v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
        Cargar más
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  PlusIcon, 
  DocumentDuplicateIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import RegistroPropiedadCard from './RegistroPropiedadCard.vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  hasMore: {
    type: Boolean,
    default: false
  }
})

const hasItems = computed(() => props.items.length > 0)

defineEmits(['create', 'edit', 'delete', 'load-more'])
</script>