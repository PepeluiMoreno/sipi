<!--
  ResizableDrawer.vue — panel lateral derecho, NO modal.
  · Se abre pegado a la derecha del contenedor (que debe ser position: relative).
  · Su borde IZQUIERDO se arrastra para ensanchar/estrechar.
  · Recuerda el ancho en localStorage (prop `storageKey`).
  · Ocupa toda la altura; el contenido (slot) gestiona su propio header/footer.
-->
<template>
  <div class="absolute top-0 right-0 h-full z-20 flex bg-white border-l border-gray-200 shadow-xl"
       :style="{ width: width + 'px' }">
    <!-- Manija de redimensión (borde izquierdo) -->
    <div class="w-1.5 h-full shrink-0 cursor-col-resize bg-transparent hover:bg-indigo-300/60 active:bg-indigo-400 transition-colors"
         :class="{ 'bg-indigo-400': dragging }" title="Arrastra para ensanchar" @mousedown.prevent="startDrag"></div>
    <div class="flex-1 min-w-0 h-full overflow-hidden"><slot /></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  storageKey: { type: String, default: 'sipi-drawer-width' },
  defaultWidth: { type: Number, default: 680 },
  minWidth: { type: Number, default: 420 },
})

const width = ref(props.defaultWidth)
const dragging = ref(false)
const maxWidth = () => Math.max(props.minWidth, Math.round(window.innerWidth * 0.92))

onMounted(() => {
  const saved = parseInt(localStorage.getItem(props.storageKey) || '', 10)
  if (Number.isFinite(saved) && saved > 0) {
    width.value = Math.min(Math.max(saved, props.minWidth), maxWidth())
  }
})

let startX = 0
let startW = 0

function startDrag(e) {
  dragging.value = true
  startX = e.clientX
  startW = width.value
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', stopDrag)
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
}

function onMove(e) {
  if (!dragging.value) return
  // arrastrar hacia la IZQUIERDA (clientX menor) ensancha
  const w = startW + (startX - e.clientX)
  width.value = Math.min(Math.max(w, props.minWidth), maxWidth())
}

function stopDrag() {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseup', stopDrag)
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  localStorage.setItem(props.storageKey, String(width.value))
}

onBeforeUnmount(stopDrag)
</script>
