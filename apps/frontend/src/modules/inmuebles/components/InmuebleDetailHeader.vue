<!-- InmuebleDetailHeader.vue -->
<template>
  <div class="sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm">
    <div class="max-w-7xl mx-auto px-6 py-4">
      <div class="flex items-center gap-6">
        <!-- Imagen -->
        <div class="w-32 h-32 flex-shrink-0 bg-gray-100 rounded-lg overflow-hidden">
          <img
            v-if="inmueble.imagen || inmueble.photo"
            :src="inmueble.imagen || inmueble.photo"
            alt=""
            class="w-full h-full object-cover"
          />
          <div v-else class="flex items-center justify-center h-full">
            <svg class="w-16 h-16 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L4 7v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V7l-8-5zm0 2.18l6 3.75V17c0 .55-.45 1-1 1H7c-.55 0-1-.45-1-1V7.93l6-3.75z"/>
              <path d="M10 14h4v5h-4z"/>
            </svg>
          </div>
        </div>

        <!-- Info principal -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <h1 class="text-2xl font-bold text-gray-900 truncate">
                {{ inmueble.denominacion_principal }}
              </h1>
              <p class="text-sm text-gray-600 mt-1">{{ inmueble.direccion }}</p>
              <p class="text-sm text-gray-500">{{ inmueble.localidad }}, {{ inmueble.provincia }}</p>
            </div>

            <!-- Badges -->
            <div class="flex flex-col items-end gap-2">
              <span
                v-if="inmueble.codigo_bien_interes_cultural || inmueble.es_bic"
                class="px-3 py-1 bg-amber-500 text-white text-sm font-semibold rounded"
              >
                BIC
              </span>
              <span
                :class="[
                  'px-3 py-1 text-sm font-semibold rounded',
                  estadoClass(inmueble.estado)
                ]"
              >
                {{ estadoLabel(inmueble.estado) }}
              </span>
              <span
                v-if="inmueble.estado_conservacion"
                :class="[
                  'px-3 py-1 text-white text-sm font-semibold rounded',
                  conservacionClass(inmueble.estado_conservacion)
                ]"
              >
                {{ conservacionLabel(inmueble.estado_conservacion) }}
              </span>
            </div>
          </div>

          <!-- Datos adicionales -->
          <div class="mt-4 grid grid-cols-4 gap-4 text-sm">
            <div>
              <span class="text-gray-500">Tipo:</span>
              <span class="ml-2 font-medium text-gray-900">{{ inmueble.tipo_inmueble }}</span>
            </div>
            <div v-if="inmueble.superficie_construida">
              <span class="text-gray-500">Sup. construida:</span>
              <span class="ml-2 font-medium text-gray-900">{{ inmueble.superficie_construida }} m²</span>
            </div>
            <div v-if="inmueble.fecha_construccion">
              <span class="text-gray-500">Año:</span>
              <span class="ml-2 font-medium text-gray-900">{{ new Date(inmueble.fecha_construccion).getFullYear() }}</span>
            </div>
            <div v-if="inmueble.codigo_bien_interes_cultural">
              <span class="text-gray-500">Código BIC:</span>
              <span class="ml-2 font-medium text-gray-900">{{ inmueble.codigo_bien_interes_cultural }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  inmueble: {
    type: Object,
    required: true
  }
})

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