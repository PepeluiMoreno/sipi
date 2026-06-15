<!-- InmuebleCard.vue — tarjeta austera (neutros + acento sobrio para BIC) -->
<template>
  <div @click="$emit('click')"
       class="card overflow-hidden cursor-pointer hover:border-zinc-300 hover:shadow transition">
    <div class="relative h-28 bg-zinc-100 flex items-center justify-center">
      <img v-if="inmueble.imagen || inmueble.photo" :src="inmueble.imagen || inmueble.photo"
           alt="" class="w-full h-full object-cover" />
      <UiIcon v-else name="inmueble" class="w-10 h-10 text-zinc-300" />

      <span v-if="inmueble.figuraProteccionActual"
            class="badge badge-warn absolute top-2 right-2">{{ inmueble.figuraProteccionActual }}</span>
    </div>

    <div class="p-3">
      <h3 class="font-semibold text-zinc-900 text-sm truncate">
        {{ inmueble.nombre || 'Sin denominación' }}
      </h3>
      <p class="text-xs text-zinc-500 truncate mt-0.5">{{ inmueble.direccion || '—' }}</p>
      <div class="flex items-center justify-between gap-2 mt-2">
        <span class="text-xs text-zinc-400 truncate">{{ localizacion }}</span>
        <span v-if="inmueble.estadoCicloVida" class="badge shrink-0">{{ estadoLabel(inmueble.estadoCicloVida) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ inmueble: { type: Object, required: true } })
defineEmits(['click'])

// Localización: "ELM – Municipio" si la entidad territorial es submunicipal; si no, municipio.
const localizacion = computed(() => {
  const et = props.inmueble.entidadTerritorial
  const muni = props.inmueble.municipio?.nombre
  let lugar = muni || ''
  if (et?.nombre && muni && et.nombre !== muni) {
    lugar = `${et.nombre} – ${muni}` // ELM – Municipio
  } else if (et?.nombre && !muni) {
    lugar = et.nombre
  }
  const prov = props.inmueble.provincia?.nombre
  return [lugar, prov].filter(Boolean).join(', ') || '—'
})

const ESTADOS = {
  no_investigado: 'No investigado', inmatriculado: 'Inmatriculado', vendido: 'Vendido',
  en_venta: 'En venta', recuperado: 'Recuperado', activo: 'Activo', en_obras: 'En obras',
  cerrado: 'Cerrado', cambio_de_uso: 'Cambio de uso', rehabilitacion: 'Rehabilitación',
}
const estadoLabel = (e) => ESTADOS[e] || e
</script>
