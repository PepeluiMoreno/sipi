<!-- UiEmptyState: estado vacío/centrado reutilizable (carga, sin datos, error). -->
<template>
  <div class="flex flex-col items-center justify-center h-full text-center text-zinc-500 p-6 gap-3">
    <UiSpinner v-if="loading" size="lg" />
    <UiIcon v-else :name="icon" size="lg" class="w-10 h-10 text-zinc-300" />
    <p class="text-sm font-medium text-zinc-600">{{ loading ? loadingText : title }}</p>
    <p v-if="!loading && description" class="text-xs text-zinc-400 max-w-xs">{{ description }}</p>
    <slot v-if="!loading" name="action" />
  </div>
</template>

<script setup>
import UiIcon from './UiIcon.vue'
import UiSpinner from './UiSpinner.vue'

defineProps({
  loading: { type: Boolean, default: false },
  loadingText: { type: String, default: 'Cargando…' },
  icon: { type: String, default: 'info' },
  title: { type: String, default: 'Sin datos' },
  description: { type: String, default: '' },
})
</script>
