<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
    <div class="flex justify-between items-start mb-3">
      <h3 class="text-lg font-semibold text-gray-900">{{ administracion.nombre }}</h3>
      <span class="px-2 py-1 text-xs rounded-full bg-indigo-100 text-indigo-800">
        {{ administracion.ambito }}
      </span>
    </div>
    
    <div class="space-y-2 text-sm text-gray-600">
      <div class="flex items-center">
        <IdentificationIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ administracion.nombreResponsable }}
      </div>
      
      <div class="flex items-center">
        <IdentificationIcon class="w-4 h-4 mr-2 text-gray-400" />
        ID: {{ administracion.numeroIdentificacion }}
      </div>
      
      <div class="flex items-center" v-if="administracion.localidad">
        <MapPinIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ administracion.localidad.nombre }}
        <span v-if="administracion.localidad.provincia">
          , {{ administracion.localidad.provincia.nombre }}
        </span>
      </div>
      
      <div class="flex items-center" v-if="administracion.telefono">
        <PhoneIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ administracion.telefono }}
      </div>
      
      <div class="flex items-center" v-if="administracion.email">
        <EnvelopeIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ administracion.email }}
      </div>
    </div>

    <div class="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center">
      <span class="text-xs text-gray-500">
        Titulares: {{ administracion.titulares?.length || 0 }}
      </span>
      <div class="flex space-x-2">
        <button 
          @click="$emit('edit', administracion.id)"
          class="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
        >
          <PencilSquareIcon class="w-4 h-4" />
        </button>
        <button 
          @click="$emit('delete', administracion.id)"
          class="p-1 text-red-600 hover:bg-red-50 rounded"
        >
          <TrashIcon class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  IdentificationIcon, 
  MapPinIcon, 
  PhoneIcon, 
  EnvelopeIcon,
  PencilSquareIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'

defineProps({
  administracion: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete'])
</script>