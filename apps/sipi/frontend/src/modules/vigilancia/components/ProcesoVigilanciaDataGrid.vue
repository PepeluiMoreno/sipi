<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <div v-if="hasItems" class="p-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <ProcesoVigilanciaCard
        v-for="p in items" :key="p.id"
        :proceso="p"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>

    <div v-else-if="!loading" class="p-12 text-center">
      <EyeIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500">No hay procesos de vigilancia</p>
    </div>

    <div v-if="loading" class="p-12 text-center">
      <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
      <p class="mt-2 text-gray-500">Cargando…</p>
    </div>

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
import { EyeIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'
import ProcesoVigilanciaCard from './ProcesoVigilanciaCard.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
  hasMore: { type: Boolean, default: false },
})
const hasItems = computed(() => props.items.length > 0)
defineEmits(['create', 'edit', 'delete', 'load-more'])
</script>
