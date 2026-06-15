<!-- ProcesoVigilanciaFiltros — FilterSidebar vertical estándar (mismo patrón que agentes). -->
<template>
  <FilterSidebar
    busqueda-placeholder="Nombre del proceso…"
    :facetas="facetas"
    @change="$emit('filter-change', $event)"
  />
</template>

<script setup>
import FilterSidebar from '../../core/components/FilterSidebar.vue'

defineEmits(['filter-change'])

// 3 opciones (≤5) → columna de checkboxes siempre visible (meta-regla del estándar).
const facetas = [
  {
    key: 'tipo',
    label: 'Tipo de vigilancia',
    tipo: 'checkboxes',
    opciones: [
      { id: 'portal_inmobiliario', nombre: 'Portales inmobiliarios' },
      { id: 'desacralizacion', nombre: 'Desacralizaciones (CEE)' },
      { id: 'prensa', nombre: 'Prensa online' },
    ],
  },
]
</script>
