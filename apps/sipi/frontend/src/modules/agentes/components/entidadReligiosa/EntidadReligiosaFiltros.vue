<!--
  EntidadReligiosaFiltros — usa el FilterSidebar VERTICAL estándar de la app.
  Solo declara sus facetas; el filtrado real lo aplica el servidor vía
  useAgenteBase → filters:[FilterInput].
-->
<template>
  <FilterSidebar
    con-geografia
    busqueda-placeholder="Nombre, NIF…"
    :facetas="facetas"
    @change="$emit('filter-change', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import FilterSidebar from '../../../core/components/FilterSidebar.vue'

const props = defineProps({
  tiposEntidad: { type: Array, default: () => [] }
})
defineEmits(['filter-change'])

const facetas = computed(() => [
  { key: 'tipoEntidadId', label: 'Tipo de entidad', tipo: 'checkboxes', opciones: props.tiposEntidad }
])
</script>
