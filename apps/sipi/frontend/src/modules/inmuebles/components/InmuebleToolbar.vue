<!-- InmuebleToolbar.vue — barra superior compacta y austera -->
<template>
  <div class="shrink-0 h-12 bg-white border-b border-zinc-200 px-4 flex items-center justify-between">
    <div class="flex items-baseline gap-2 min-w-0">
      <h1 class="text-base font-semibold text-zinc-900">Inmuebles</h1>
      <span class="text-sm text-zinc-400">{{ total }} resultados</span>
    </div>

    <div class="flex items-center gap-2">
      <!-- Selector de vista (segmentado) -->
      <div class="flex items-center bg-zinc-100 rounded p-0.5">
        <button
          v-for="opt in vistas" :key="opt.value"
          @click="cambiarVista(opt.value)"
          :title="opt.label"
          :class="['btn-icon transition-colors',
                   localView === opt.value ? 'bg-white text-zinc-900 shadow-sm' : 'text-zinc-500 hover:text-zinc-800']"
        >
          <UiIcon :name="opt.icon" size="sm" />
        </button>
      </div>

      <UiButton variant="primary" icon="plus" @click="$emit('nuevo')">Nuevo inmueble</UiButton>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  view: { type: String, default: 'cards' },
  total: { type: Number, default: 0 },
})
const emit = defineEmits(['update:view', 'nuevo'])

const vistas = [
  { value: 'cards', icon: 'cards', label: 'Tarjetas' },
  { value: 'mapa', icon: 'mapa', label: 'Mapa' },
]

const localView = ref(props.view)
watch(() => props.view, v => { localView.value = v })

const cambiarVista = (vista) => {
  localView.value = vista
  emit('update:view', vista)
}
</script>
