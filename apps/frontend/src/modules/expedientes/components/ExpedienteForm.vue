<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" @click.self="$emit('cerrar')">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ modelo.id ? 'Editar expediente' : 'Nuevo expediente' }}
        </h3>
        <button @click="$emit('cerrar')" class="text-gray-400 hover:text-gray-600">✕</button>
      </div>

      <div class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de expediente</label>
          <select v-model="modelo.tipoExpedienteId" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="" disabled>Seleccione…</option>
            <option v-for="t in tipos" :key="t.id" :value="t.id">{{ t.nombre }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Título</label>
          <input v-model="modelo.titulo" type="text" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha inicio</label>
            <input v-model="modelo.fechaInicio" type="date" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha fin</label>
            <input v-model="modelo.fechaFin" type="date" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Importe (€)</label>
            <input v-model="modelo.importe" type="number" step="0.01" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Estado</label>
            <select v-model="modelo.estado" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="borrador">borrador</option>
              <option value="propuesto">propuesto</option>
              <option value="confirmado">confirmado</option>
              <option value="descartado">descartado</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea v-model="modelo.descripcion" rows="3" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"></textarea>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Referencia externa</label>
            <input v-model="modelo.referenciaExterna" type="text" placeholder="decreto, código BDNS, RC…"
                   class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Enlace</label>
            <input v-model="modelo.enlace" type="url" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200">
        <button @click="$emit('cerrar')" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancelar</button>
        <button @click="guardar" :disabled="!modelo.tipoExpedienteId || loading"
                class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm disabled:opacity-50">
          {{ loading ? 'Guardando…' : 'Guardar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useExpedientes } from '../composables/useExpedientes'

const props = defineProps({
  inmuebleId: { type: String, required: true },
  expediente: { type: Object, default: null }
})
const emit = defineEmits(['cerrar', 'guardado'])

const { crear, actualizar, listarTipos, loading } = useExpedientes()
const tipos = ref([])

const modelo = reactive({
  id: props.expediente?.id || null,
  tipoExpedienteId: props.expediente?.tipoExpedienteId || '',
  titulo: props.expediente?.titulo || '',
  fechaInicio: (props.expediente?.fechaInicio || '').slice(0, 10),
  fechaFin: (props.expediente?.fechaFin || '').slice(0, 10),
  importe: props.expediente?.importe ?? null,
  estado: props.expediente?.estado || 'borrador',
  descripcion: props.expediente?.descripcion || '',
  referenciaExterna: props.expediente?.referenciaExterna || '',
  enlace: props.expediente?.enlace || ''
})

onMounted(async () => { tipos.value = await listarTipos() })

async function guardar() {
  const payload = {
    inmuebleId: props.inmuebleId,
    tipoExpedienteId: modelo.tipoExpedienteId,
    titulo: modelo.titulo || null,
    fechaInicio: modelo.fechaInicio || null,
    fechaFin: modelo.fechaFin || null,
    importe: modelo.importe !== '' && modelo.importe != null ? Number(modelo.importe) : null,
    estado: modelo.estado || null,
    descripcion: modelo.descripcion || null,
    referenciaExterna: modelo.referenciaExterna || null,
    enlace: modelo.enlace || null
  }
  if (modelo.id) await actualizar({ id: modelo.id, ...payload })
  else await crear(payload)
  emit('guardado')
  emit('cerrar')
}
</script>
