<!--
  AgenteCrudShell.vue — layout MAESTRO-DETALLE estándar para vistas CRUD.
  Izquierda: panel de filtros (slot #filtros, normalmente un FilterSidebar).
  Centro: cabecera (título + total + botón "Nuevo", SIEMPRE aquí) y, debajo, la LISTA (#lista).
  Detalle/edición: el slot #form se abre en un DRAWER DERECHO redimensionable y persistente
  (ResizableDrawer) — sin modales. El contenido derecho llena el ancho disponible.
-->
<template>
  <div class="flex h-full min-h-0">
    <slot name="filtros" />

    <main class="flex-1 min-h-0 flex flex-col overflow-hidden relative">
      <div class="shrink-0 h-11 px-4 flex items-center justify-between border-b border-gray-200 bg-white">
        <div class="flex items-baseline gap-3 min-w-0">
          <h1 class="text-base font-semibold text-gray-900 truncate">{{ titulo }}</h1>
          <span v-if="total != null" class="text-xs text-gray-500 shrink-0">
            {{ Number(total).toLocaleString('es-ES') }}
          </span>
        </div>
        <button v-if="!editando" @click="$emit('nuevo')"
                class="inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 shrink-0">
          <PlusIcon class="w-4 h-4" /> {{ nuevoLabel }}
        </button>
      </div>

      <!-- Lista: llena el área disponible -->
      <div class="flex-1 min-h-0 overflow-auto p-4">
        <slot name="lista" />
      </div>

      <!-- Detalle/edición en drawer derecho redimensionable -->
      <ResizableDrawer v-if="editando" :storage-key="drawerKey">
        <slot name="form" />
      </ResizableDrawer>
    </main>
  </div>
</template>

<script setup>
import { PlusIcon } from '@heroicons/vue/24/outline'
import ResizableDrawer from './ui/ResizableDrawer.vue'

defineProps({
  titulo: { type: String, default: '' },
  total: { type: [Number, null], default: null },
  editando: { type: Boolean, default: false },
  nuevoLabel: { type: String, default: 'Nuevo' },
  drawerKey: { type: String, default: 'sipi-crud-drawer' },
})
defineEmits(['nuevo'])
</script>
