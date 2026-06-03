<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
    <div class="flex justify-between items-start mb-3">
      <h3 class="text-lg font-semibold text-gray-900">{{ registro.nombre }}</h3>
      <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
        Registro
      </span>
    </div>
    
    <div class="space-y-2 text-sm text-gray-600">
      <div class="flex items-center">
        <IdentificationIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ registro.nombreRegistrador }}
      </div>
      
      <div class="flex items-center">
        <IdentificationIcon class="w-4 h-4 mr-2 text-gray-400" />
        ID: {{ registro.numeroIdentificacion }}
      </div>
      
      <div class="flex items-center" v-if="registro.municipio">
        <MapPinIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ registro.municipio.nombre }}
        <span v-if="registro.municipio.provincia">
          , {{ registro.municipio.provincia.nombre }}
        </span>
      </div>
      
      <div class="flex items-center" v-if="registro.telefono">
        <PhoneIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ registro.telefono }}
      </div>
      
      <div class="flex items-center" v-if="registro.email">
        <EnvelopeIcon class="w-4 h-4 mr-2 text-gray-400" />
        {{ registro.email }}
      </div>
    </div>

    <div class="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center">
      <span class="text-xs text-gray-500">
        Titulares: {{ registro.titulares?.length || 0 }}
      </span>
      <div class="flex space-x-2">
        <button 
          @click="$emit('edit', registro.id)"
          class="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
        >
          <PencilSquareIcon class="w-4 h-4" />
        </button>
        <button 
          @click="$emit('delete', registro.id)"
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
  registro: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete'])
</script>