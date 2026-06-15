<!--
  AgenteCrudShell.vue — layout MAESTRO-DETALLE estándar para vistas de agentes/entidades.
  Izquierda: panel de filtros (slot #filtros, normalmente un FilterSidebar escamoteable).
  Derecha: cabecera (título + total + "Nuevo") y, debajo, la LISTA (slot #lista) o,
  en modo edición, el FORMULARIO inline (slot #form) — sin modales.
  El contenido derecho es flex-1 → se adapta al ancho disponible cuando el filtro se oculta.
-->
<template>
  <div class="flex h-full min-h-0">
    <slot name="filtros" />

    <main class="flex-1 min-h-0 flex flex-col overflow-hidden">
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

      <div class="flex-1 min-h-0 overflow-hidden flex flex-col gap-3 p-4">
        <!-- Lista: ocupa todo; al consultar/editar se encoge para ver solo el registro seleccionado.
             En alta nueva (editando sin selección) se oculta para dejar todo el espacio al formulario. -->
        <div v-if="!editando || seleccion" :class="editando ? 'shrink-0' : 'flex-1 min-h-0 overflow-auto'">
          <slot name="lista" />
        </div>
        <!-- Formulario (consulta/edición/alta): aparece debajo, mismo ancho -->
        <div v-if="editando" class="flex-1 min-h-0 overflow-auto">
          <slot name="form" />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { PlusIcon } from '@heroicons/vue/24/outline'

defineProps({
  titulo: { type: String, default: '' },
  total: { type: [Number, null], default: null },
  editando: { type: Boolean, default: false },
  nuevoLabel: { type: String, default: 'Nuevo' }
})
defineEmits(['nuevo'])
</script>
