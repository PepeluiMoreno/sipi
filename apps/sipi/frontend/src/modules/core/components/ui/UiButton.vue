<!-- UiButton: botón estándar con variantes austeras e icono opcional. -->
<template>
  <button :type="type" :disabled="disabled || loading" :class="['btn', variantClass]">
    <UiSpinner v-if="loading" size="sm" />
    <UiIcon v-else-if="icon" :name="icon" size="sm" />
    <span v-if="$slots.default"><slot /></span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import UiIcon from './UiIcon.vue'
import UiSpinner from './UiSpinner.vue'

const props = defineProps({
  variant: { type: String, default: 'secondary' }, // primary | secondary | ghost | danger
  icon: { type: String, default: '' },
  type: { type: String, default: 'button' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})
const variantClass = computed(() => `btn-${props.variant}`)
</script>
