<!-- UiSpinner: indicador de carga sobrio (neutro, sin colorines). -->
<template>
  <svg :class="['animate-spin text-zinc-400', sizeClass]" viewBox="0 0 24 24" fill="none" aria-label="Cargando">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
    <path class="opacity-90" fill="currentColor"
          d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ size: { type: String, default: 'md' } })
const sizeClass = computed(() => ({ sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-9 h-9' }[props.size] || 'w-6 h-6'))
</script>
