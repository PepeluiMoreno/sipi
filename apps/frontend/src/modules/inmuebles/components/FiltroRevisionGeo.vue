<!-- FiltroRevisionGeo.vue
     Control de filtro para aislar los inmuebles que necesitan revisión manual
     de geolocalización. Se integra en el objeto `filters` que ya usáis en
     InmueblesView (v-model:filters).

     Tres estados (segmented):
       - todos
       - requieren revisión  -> filters.requiere_revision = true
       - mejorables (resueltos a baja precisión, p.ej. solo centroide municipal)
                              -> filters.precision_geo = 'MUNICIPIO'
-->
<template>
  <div class="inline-flex rounded-lg border border-gray-200 overflow-hidden text-sm">
    <button
      v-for="op in opciones" :key="op.valor"
      class="px-3 py-1.5 transition-colors"
      :class="seleccion === op.valor ? 'bg-gray-800 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
      @click="aplicar(op.valor)"
    >
      {{ op.etiqueta }}
      <span v-if="op.valor !== 'todos' && conteo?.[op.valor] != null"
            class="ml-1 text-xs opacity-70">({{ conteo[op.valor] }})</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) }, // el objeto `filters`
  conteo: { type: Object, default: null },           // { revision: n, mejorables: n } opcional, para badges
})
const emit = defineEmits(['update:modelValue'])

const opciones = [
  { valor: 'todos',     etiqueta: 'Todos' },
  { valor: 'revision',  etiqueta: 'Requieren revisión' },
  { valor: 'mejorables',etiqueta: 'Baja precisión' },
]
const seleccion = ref('todos')

function aplicar(valor) {
  seleccion.value = valor
  const f = { ...props.modelValue }
  delete f.requiere_revision
  delete f.precision_geo
  if (valor === 'revision') f.requiere_revision = true
  if (valor === 'mejorables') f.precision_geo = 'MUNICIPIO'
  emit('update:modelValue', f)
}
</script>
