<!-- AdministracionFiltros — FilterSidebar vertical estándar. -->
<template>
  <FilterSidebar
    con-geografia
    busqueda-placeholder="Nombre, NIF…"
    :facetas="facetas"
    @change="$emit('filter-change', $event)"
  />
</template>

<script setup>
import FilterSidebar from '../../../core/components/FilterSidebar.vue'

defineEmits(['filter-change'])

// 4 opciones (≤5) → columna de checkboxes siempre visible (meta-regla).
const facetas = [
  {
    key: 'ambito',
    label: 'Ámbito',
    tipo: 'checkboxes',
    opciones: [
      { id: 'municipal', nombre: 'Municipal' },
      { id: 'provincial', nombre: 'Provincial' },
      { id: 'autonomico', nombre: 'Autonómico' },
      { id: 'estatal', nombre: 'Estatal' }
    ]
  }
]
</script>
