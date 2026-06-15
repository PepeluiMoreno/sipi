<!-- NotariaFiltros — FilterSidebar vertical estándar (búsqueda + geografía). -->
<template>
  <FilterSidebar
    con-geografia
    busqueda-placeholder="Nombre, NIF…"
    @change="$emit('filter-change', $event)"
  />
</template>

<script setup>
import FilterSidebar from '../../../core/components/FilterSidebar.vue'
defineEmits(['filter-change'])
</script>
