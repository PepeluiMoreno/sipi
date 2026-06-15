<!-- InmuebleDetailHeader.vue — resumen compacto del inmueble (media anchura, comparte banda con las solapas) -->
<template>
  <div class="flex items-center gap-3 min-w-0 py-2">
    <!-- Miniatura -->
    <div class="w-12 h-12 shrink-0 bg-zinc-100 rounded overflow-hidden flex items-center justify-center">
      <img v-if="inmueble.imagen || inmueble.photo" :src="inmueble.imagen || inmueble.photo"
           alt="" class="w-full h-full object-cover" />
      <UiIcon v-else name="inmueble" class="w-6 h-6 text-zinc-300" />
    </div>

    <!-- Nombre + dirección -->
    <div class="flex-1 min-w-0">
      <h1 class="text-base font-semibold text-zinc-900 truncate leading-tight">
        {{ inmueble.denominacion_principal }}
      </h1>
      <p class="text-xs text-zinc-500 truncate">{{ inmueble.direccion }}</p>
      <p v-if="inmueble.localidad || inmueble.provincia" class="text-xs text-zinc-400 truncate">
        {{ [inmueble.localidad, inmueble.provincia].filter(Boolean).join(', ') }}
      </p>
      <p v-if="pedania" class="text-xs text-primary-600 truncate">Pedanía: {{ pedania }}</p>
    </div>

    <!-- Badges -->
    <div class="flex items-center gap-1.5 shrink-0">
      <span v-if="inmueble.codigo_bien_interes_cultural || inmueble.es_bic" class="badge badge-warn">BIC</span>
      <span v-if="inmueble.estado" class="badge">{{ estadoLabel(inmueble.estado) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  inmueble: {
    type: Object,
    required: true
  }
})

// Entidad local menor (pedanía) del inmueble, si la tiene (dato real o mock).
const pedania = computed(() =>
  props.inmueble.entidadLocalMenor?.nombre || props.inmueble.entidad_local_menor?.nombre || props.inmueble.pedania || '')

const estadoLabel = (estado) => {
  const labels = {
    no_investigado: 'No investigado',
    inmatriculado: 'Inmatriculado',
    vendido: 'Vendido',
    en_venta: 'En venta',
    recuperado: 'Recuperado',
    activo: 'Activo',
    en_obras: 'En obras',
    cerrado: 'Cerrado'
  }
  return labels[estado] || estado
}
</script>
