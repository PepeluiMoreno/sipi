<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
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
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center">
      <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
      <p class="mt-2 text-gray-500">Cargando...</p>
    </div>

    <!-- Pie: contador + cargar más -->
    <div v-if="hasItems" class="p-3 border-t border-gray-200 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        Mostrando {{ items.length.toLocaleString('es-ES') }} de {{ total.toLocaleString('es-ES') }}
      </div>
      <button v-if="hasMore" @click="$emit('load-more')" :disabled="loading"
              class="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50">
        Cargar más
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  BuildingOfficeIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import AdministracionCard from './AdministracionCard.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
  hasMore: { type: Boolean, default: false }
})

const hasItems = computed(() => props.items.length > 0)

defineEmits(['create', 'edit', 'delete', 'load-more'])
</script>