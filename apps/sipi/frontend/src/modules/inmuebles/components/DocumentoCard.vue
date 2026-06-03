<!-- DocumentoCard.vue -->
<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
    <span class="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded mb-3">
      {{ documento.tipo }}
    </span>

    <div class="flex gap-4">
      <div class="w-20 h-24 flex-shrink-0 bg-gray-100 rounded overflow-hidden">
        <img v-if="documento.thumbnail" :src="documento.thumbnail" alt="" class="w-full h-full object-cover" />
        <div v-else class="flex items-center justify-center h-full">
          <DocumentIcon class="w-8 h-8 text-gray-400" />
        </div>
      </div>

      <div class="flex-1 min-w-0">
        <h4 class="font-medium text-sm text-gray-900 truncate mb-1">{{ documento.nombre }}</h4>
        <div class="space-y-0.5 text-xs text-gray-600">
          <p>{{ documento.formato }} • {{ formatSize(documento.tamanio) }}</p>
          <p>Pub: {{ formatFecha(documento.fecha_publicacion) }}</p>
          <p>Subido: {{ formatFecha(documento.fecha_inclusion) }}</p>
          <p class="text-gray-500">Por: {{ documento.usuario }}</p>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <button @click="$emit('view', documento)" class="p-1 hover:bg-gray-100 rounded" title="Ver">
          <EyeIcon class="w-4 h-4 text-gray-600" />
        </button>
        <button @click="$emit('download', documento)" class="p-1 hover:bg-gray-100 rounded" title="Descargar">
          <ArrowDownTrayIcon class="w-4 h-4 text-gray-600" />
        </button>
        <button @click="$emit('delete', documento)" class="p-1 hover:bg-red-50 rounded" title="Eliminar">
          <TrashIcon class="w-4 h-4 text-red-600" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { DocumentIcon, EyeIcon, ArrowDownTrayIcon, TrashIcon } from '@heroicons/vue/24/outline'

defineProps({
  documento: {
    type: Object,
    required: true
  }
})

defineEmits(['view', 'download', 'delete'])

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatFecha = (fecha) => {
  if (!fecha) return '-'
  return new Date(fecha).toLocaleDateString('es-ES')
}
</script>