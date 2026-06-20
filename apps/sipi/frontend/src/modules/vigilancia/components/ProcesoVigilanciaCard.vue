<!-- ProcesoVigilanciaCard — tarjeta de proceso (mismo lenguaje visual que las cards de agentes). -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-4 hover:border-indigo-300 hover:shadow-sm transition cursor-pointer flex flex-col gap-2"
       @click="$emit('edit', proceso.id)">
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <h3 class="font-medium text-gray-900 truncate">{{ proceso.nombre || '(sin nombre)' }}</h3>
        <p class="text-xs text-gray-500">{{ tipoLabel(proceso.tipo) }}</p>
      </div>
      <span class="shrink-0 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
            :class="proceso.activo ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-500'">
        <span class="w-1.5 h-1.5 rounded-full" :class="proceso.activo ? 'bg-emerald-500' : 'bg-gray-400'"></span>
        {{ proceso.activo ? 'Activo' : 'Pausado' }}
      </span>
    </div>
    <div class="flex items-center gap-3 text-xs text-gray-500">
      <span class="inline-flex items-center gap-1"><ClockIcon class="w-3.5 h-3.5" />{{ humanizar(proceso.frecuenciaCron) }}</span>
      <span v-if="nFuentes">· {{ nFuentes }} fuente{{ nFuentes === 1 ? '' : 's' }}</span>
    </div>
    <div class="flex justify-end">
      <button @click.stop="$emit('delete', proceso.id)" class="text-gray-400 hover:text-red-600 text-xs">Eliminar</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ClockIcon } from '@heroicons/vue/24/outline'
import { tipoLabel } from '../catalog/vigilanciaCatalog'
import { humanizar } from '../catalog/frecuencias'

const props = defineProps({ proceso: { type: Object, required: true } })
defineEmits(['edit', 'delete'])

const nFuentes = computed(() => (props.proceso?.parametros?.fuentes || []).length)
</script>
