<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex items-center">
          <ExclamationTriangleIcon class="w-6 h-6 text-red-600 mr-3" />
          <h2 class="text-lg font-semibold text-gray-900">Confirmar eliminación</h2>
        </div>
      </div>

      <!-- Contenido -->
      <div class="p-6">
        <p class="text-gray-700 mb-4">
          ¿Estás seguro de que quieres eliminar a
          <span class="font-semibold">{{ getItemName() }}</span>?
        </p>
        
        <div v-if="itemType === 'role'" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div class="flex">
            <ExclamationCircleIcon class="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
            <p class="text-sm text-yellow-700">
              <span class="font-semibold">Advertencia:</span> 
              Este rol está asignado a {{ item.usuarios_count }} usuarios. 
              La eliminación podría afectar sus permisos.
            </p>
          </div>
        </div>

        <div v-else-if="itemType === 'user'" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div class="flex">
            <ExclamationCircleIcon class="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
            <p class="text-sm text-yellow-700">
              <span class="font-semibold">Advertencia:</span> 
              Esta acción no se puede deshacer. El usuario perderá el acceso al sistema.
            </p>
          </div>
        </div>
      </div>

      <!-- Botones -->
      <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
        <button
          type="button"
          @click="$emit('cancel')"
          class="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
        >
          Cancelar
        </button>
        <button
          type="button"
          @click="$emit('confirm')"
          class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Eliminar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ExclamationTriangleIcon, ExclamationCircleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  item: Object,
  itemType: String
})

defineEmits(['confirm', 'cancel'])

const getItemName = () => {
  if (!props.item) return ''
  
  if (props.itemType === 'user') {
    return `${props.item.nombre} ${props.item.apellidos}`
  } else if (props.itemType === 'role') {
    return props.item.nombre
  }
  
  return ''
}
</script>