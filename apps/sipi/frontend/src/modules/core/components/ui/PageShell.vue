<!-- PageShell: contenedor de página a ALTURA COMPLETA (sin scroll de página).
     Cabecera fija opcional + cuerpo que ocupa el resto. Las vistas colocan dentro
     paneles cuyo cuerpo scrollea internamente si hace falta. -->
<template>
  <div class="h-full min-h-0 flex flex-col">
    <header v-if="title || $slots.title || $slots.actions"
            class="shrink-0 h-12 px-4 flex items-center justify-between border-b border-zinc-200 bg-white">
      <div class="flex items-center gap-2 min-w-0">
        <UiIcon v-if="icon" :name="icon" class="text-zinc-400" />
        <slot name="title">
          <h2 class="text-base font-semibold text-zinc-900 truncate">{{ title }}</h2>
        </slot>
        <span v-if="subtitle" class="text-sm text-zinc-400 truncate">· {{ subtitle }}</span>
      </div>
      <div class="flex items-center gap-2"><slot name="actions" /></div>
    </header>
    <div :class="['flex-1 min-h-0', padded ? 'p-4' : '']">
      <slot />
    </div>
  </div>
</template>

<script setup>
import UiIcon from './UiIcon.vue'
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: '' },
  padded: { type: Boolean, default: true },
})
</script>
