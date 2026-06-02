<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-red-200 bg-red-50">
        <div class="flex items-center">
          <ExclamationTriangleIcon class="w-6 h-6 text-red-600 mr-3" />
          <h2 class="text-lg font-semibold text-red-900">
            Backend no disponible
          </h2>
        </div>
      </div>

      <!-- Contenido -->
      <div class="p-6">
        <p class="text-gray-700 mb-4">
          {{ message }}
        </p>
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p class="text-sm text-yellow-700">
            <span class="font-semibold">Modo desarrollo:</span> Usando datos de prueba. Las operaciones se simularán localmente.
          </p>
        </div>
        <p class="text-xs text-gray-500 mt-4">
          Si estás en producción, verifica la configuración de Apollo Client.
        </p>
      </div>

      <!-- Botones -->
      <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Entendido
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
defineEmits(['close'])
defineProps({
  message: {
    type: String,
    default: 'No se pudo conectar con el servidor GraphQL. El sistema funcionará en modo simulado.'
  }
})
</script>