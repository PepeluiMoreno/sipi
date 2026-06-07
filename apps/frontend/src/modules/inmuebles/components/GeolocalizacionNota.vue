<!-- GeolocalizacionNota.vue
     Nota de exactitud de la geolocalización de un inmueble.
     Se apoya en dos ejes independientes:
       - precision_geo : EDIFICIO | NUCLEO | MUNICIPIO | SIN_UBICAR  (qué de exacto)
       - fuente_coordenadas : MANUAL | OSM | CATASTRO | WIKIDATA | GEOCODER | INE_PADRON (de dónde)
     y un estado de confirmación opcional (candidato OSM sin confirmar).
-->
<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border"
    :class="estilo.clase"
    :title="tooltip"
  >
    <span class="w-2 h-2 rounded-full" :class="estilo.punto"></span>
    {{ estilo.texto }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  precisionGeo: { type: String, default: null },        // EDIFICIO | NUCLEO | MUNICIPIO | SIN_UBICAR
  fuenteCoordenadas: { type: String, default: null },   // MANUAL | OSM | CATASTRO | WIKIDATA | GEOCODER | INE_PADRON
  confianza: { type: String, default: null },           // alta | media
  osmEstado: { type: String, default: null },           // candidato_confirmar | auto_aceptado | null
})

const MAPA = {
  EDIFICIO:  { texto: 'Ubicación exacta (edificio)',        clase: 'bg-green-50 text-green-700 border-green-200',   punto: 'bg-green-500' },
  NUCLEO:    { texto: 'Aproximada — núcleo de población',   clase: 'bg-amber-50 text-amber-700 border-amber-200',   punto: 'bg-amber-500' },
  MUNICIPIO: { texto: 'Aproximada — centro del municipio',  clase: 'bg-orange-50 text-orange-700 border-orange-200', punto: 'bg-orange-500' },
  SIN_UBICAR:{ texto: 'Sin geolocalizar',                   clase: 'bg-gray-100 text-gray-600 border-gray-200',     punto: 'bg-gray-400' },
}
const FUENTE = { MANUAL:'manual', OSM:'OpenStreetMap', CATASTRO:'Catastro', WIKIDATA:'Wikidata', GEOCODER:'geocodificador', INE_PADRON:'padrón INE' }

const estilo = computed(() => {
  if (props.osmEstado === 'candidato_confirmar')
    return { texto: 'Por confirmar', clase: 'bg-sky-50 text-sky-700 border-sky-200 border-dashed', punto: 'bg-sky-500' }
  return MAPA[props.precisionGeo] || MAPA.SIN_UBICAR
})

const tooltip = computed(() => {
  const partes = []
  if (props.fuenteCoordenadas) partes.push(`Fuente: ${FUENTE[props.fuenteCoordenadas] || props.fuenteCoordenadas}`)
  if (props.confianza) partes.push(`Confianza: ${props.confianza}`)
  if (props.osmEstado === 'candidato_confirmar') partes.push('Coincidencia OSM sin confirmar — requiere revisión manual')
  return partes.join(' · ')
})
</script>
