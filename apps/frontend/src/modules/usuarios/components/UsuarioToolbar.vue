<template>
  <div class="bg-white rounded-lg border border-gray-200 p-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div class="flex-1">
        <div class="relative max-w-md">
          <MagnifyingGlassIcon class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            :value="busqueda"
            @input="$emit('update-busqueda', $event.target.value)"
            type="text"
            placeholder="Buscar usuarios por nombre, email o localidad..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            :disabled="usuarioSeleccionado"
          >
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <div class="text-sm text-gray-500">
          {{ totalResultados }} resultados
        </div>
        <button
          @click="$emit('reset-filtros')"
          class="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
          :disabled="usuarioSeleccionado"
          :class="{ 'opacity-50 cursor-not-allowed': usuarioSeleccionado }"
        >
          Limpiar filtros
        </button>
        <button
          @click="$emit('nuevo-usuario')"
          class="bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center text-sm font-medium"
          :disabled="usuarioSeleccionado"
          :class="{ 'opacity-50 cursor-not-allowed': usuarioSeleccionado }"
        >
          <PlusIcon class="w-4 h-4 mr-1" />
          Nuevo
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { MagnifyingGlassIcon, PlusIcon } from '@heroicons/vue/24/outline'

defineProps({
  totalResultados: {
    type: Number,
    default: 0
  },
  busqueda: {
    type: String,
    default: ''
  },
  usuarioSeleccionado: {
    type: Object,
    default: null
  }
})

defineEmits(['update-busqueda', 'reset-filtros', 'nuevo-usuario'])
</script>