<!-- InmuebleToolbar.vue -->
<template>
  <div class="bg-white border-b border-gray-200 px-6 py-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <h1 class="text-xl font-semibold text-gray-900">Inmuebles</h1>
        <span class="text-sm text-gray-500">{{ total }} resultados</span>
      </div>

      <div class="flex items-center space-x-3">
        <!-- Selector vista -->
        <div class="flex bg-gray-100 rounded-lg p-1">
          <button
            @click="cambiarVista('cards')"
            :class="[
              'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              localView === 'cards' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            @click="cambiarVista('mapa')"
            :class="[
              'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              localView === 'mapa' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          </button>
        </div>

        <!-- Botón nuevo -->
        <button
          @click="$emit('nuevo')"
          class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Nuevo inmueble</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  view: {
    type: String,
    default: 'cards'
  },
  total: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:view', 'nuevo'])

const localView = ref(props.view)

watch(() => props.view, (newVal) => {
  localView.value = newVal
})

const cambiarVista = (vista) => {
  localView.value = vista
  emit('update:view', vista)
}
</script>