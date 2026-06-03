<!-- InmuebleCard.vue -->
<template>
  <div
    @click="$emit('click')"
    class="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
  >
    <div class="relative h-32 bg-gray-100">
      <img
        v-if="inmueble.imagen || inmueble.photo"
        :src="inmueble.imagen || inmueble.photo"
        alt=""
        class="w-full h-full object-cover"
      />
      <div v-else class="flex items-center justify-center h-full">
        <svg class="w-12 h-12 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L4 7v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V7l-8-5zm0 2.18l6 3.75V17c0 .55-.45 1-1 1H7c-.55 0-1-.45-1-1V7.93l6-3.75z"/>
          <path d="M10 14h4v5h-4z"/>
        </svg>
      </div>

      <div class="absolute top-2 right-2 flex flex-col gap-1">
        <span
          v-if="inmueble.codigo_bien_interes_cultural || inmueble.es_bic"
          class="px-2 py-0.5 bg-amber-500 text-white text-xs font-semibold rounded"
        >
          BIC
        </span>
        <span
          :class="[
            'px-2 py-0.5 text-xs font-semibold rounded',
            estadoClass(inmueble.estado)
          ]"
        >
          {{ estadoLabel(inmueble.estado) }}
        </span>
        <span
          v-if="inmueble.estado_conservacion"
          :class="[
            'px-2 py-0.5 text-white text-xs font-semibold rounded',
            conservacionClass(inmueble.estado_conservacion)
          ]"
        >
          {{ conservacionLabel(inmueble.estado_conservacion) }}
        </span>
      </div>
    </div>

    <div class="p-3">
      <h3 class="font-semibold text-gray-900 text-sm truncate mb-1">
        {{ inmueble.denominacion_principal }}
      </h3>
      <p class="text-xs text-gray-600 truncate">
        {{ inmueble.direccion }}
      </p>
      <p class="text-xs text-gray-500 mt-1">
        {{ inmueble.localidad }}, {{ inmueble.provincia }}
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  inmueble: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

const estadoClass = (estado) => {
  const classes = {
    'no_investigado': 'bg-gray-100 text-gray-800',
    'inmatriculado': 'bg-green-100 text-green-800',
    'vendido': 'bg-yellow-100 text-yellow-800',
    'en_venta': 'bg-red-100 text-red-800',
    'recuperado': 'bg-blue-100 text-blue-800',
    'activo': 'bg-green-100 text-green-800',
    'en_obras': 'bg-orange-100 text-orange-800',
    'cerrado': 'bg-gray-100 text-gray-800'
  }
  return classes[estado] || 'bg-gray-100 text-gray-800'
}

const estadoLabel = (estado) => {
  const labels = {
    'no_investigado': 'No investigado',
    'inmatriculado': 'Inmatriculado',
    'vendido': 'Vendido',
    'en_venta': 'En venta',
    'recuperado': 'Recuperado',
    'activo': 'Activo',
    'en_obras': 'En obras',
    'cerrado': 'Cerrado'
  }
  return labels[estado] || estado
}

const conservacionClass = (conservacion) => {
  const classes = {
    'excelente': 'bg-green-600',
    'bueno': 'bg-blue-600',
    'regular': 'bg-yellow-600',
    'malo': 'bg-orange-600',
    'ruina': 'bg-red-600'
  }
  return classes[conservacion] || 'bg-gray-600'
}

const conservacionLabel = (conservacion) => {
  const labels = {
    'excelente': 'Excelente',
    'bueno': 'Bueno',
    'regular': 'Regular',
    'malo': 'Malo',
    'ruina': 'Ruina'
  }
  return labels[conservacion] || conservacion
}
</script>