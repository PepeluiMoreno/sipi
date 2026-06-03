<!-- InmuebleCard.vue — tarjeta austera (neutros + acento sobrio para BIC) -->
<template>
  <div @click="$emit('click')"
       class="card overflow-hidden cursor-pointer hover:border-zinc-300 hover:shadow transition">
    <div class="relative h-28 bg-zinc-100 flex items-center justify-center">
      <img v-if="inmueble.imagen || inmueble.photo" :src="inmueble.imagen || inmueble.photo"
           alt="" class="w-full h-full object-cover" />
      <UiIcon v-else name="inmueble" class="w-10 h-10 text-zinc-300" />

      <span v-if="inmueble.codigo_bien_interes_cultural || inmueble.es_bic"
            class="badge badge-warn absolute top-2 right-2">BIC</span>
    </div>

    <div class="p-3">
      <h3 class="font-semibold text-zinc-900 text-sm truncate">
        {{ inmueble.denominacion_principal || inmueble.nombre || 'Sin denominación' }}
      </h3>
      <p class="text-xs text-zinc-500 truncate mt-0.5">{{ inmueble.direccion || '—' }}</p>
      <div class="flex items-center justify-between gap-2 mt-2">
        <span class="text-xs text-zinc-400 truncate">
          {{ [inmueble.localidad, inmueble.provincia].filter(Boolean).join(', ') || '—' }}
        </span>
        <span v-if="inmueble.estado" class="badge shrink-0">{{ estadoLabel(inmueble.estado) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ inmueble: { type: Object, required: true } })
defineEmits(['click'])

const ESTADOS = {
  no_investigado: 'No investigado', inmatriculado: 'Inmatriculado', vendido: 'Vendido',
  en_venta: 'En venta', recuperado: 'Recuperado', activo: 'Activo', en_obras: 'En obras',
  cerrado: 'Cerrado', cambio_de_uso: 'Cambio de uso', rehabilitacion: 'Rehabilitación',
}
const estadoLabel = (e) => ESTADOS[e] || e
</script>
