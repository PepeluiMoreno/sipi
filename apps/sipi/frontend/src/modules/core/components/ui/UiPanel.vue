<!-- UiPanel: superficie con cabecera fija y cuerpo que ocupa el alto disponible.
     Pensado para layouts sin scroll de página: el cuerpo scrollea internamente. -->
<template>
  <section class="panel h-full">
    <header v-if="title || $slots.header || $slots.actions" class="panel-header">
      <div class="flex items-center gap-2 min-w-0">
        <UiIcon v-if="icon" :name="icon" size="sm" class="text-zinc-400" />
        <slot name="header"><span class="truncate">{{ title }}</span></slot>
      </div>
      <div class="flex items-center gap-1"><slot name="actions" /></div>
    </header>
    <div :class="['panel-body', bodyClass]">
      <slot />
    </div>
  </section>
</template>

<script setup>
import UiIcon from './UiIcon.vue'
defineProps({
  title: { type: String, default: '' },
  icon: { type: String, default: '' },
  bodyClass: { type: String, default: '' },
})
</script>
