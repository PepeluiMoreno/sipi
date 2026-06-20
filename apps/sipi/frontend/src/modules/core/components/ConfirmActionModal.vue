<!-- ConfirmActionModal.vue — modal de confirmación (adaptado de SIGA, paleta SIPI) -->
<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-zinc-900/40" @click="cancelar" />
      <div class="relative bg-white rounded-xl shadow-card max-w-md w-full p-6">
        <div class="flex items-center justify-center w-12 h-12 rounded-full mx-auto mb-4" :class="v.fondo">
          <component :is="v.icon" class="w-6 h-6" :class="v.color" />
        </div>
        <h3 class="text-base font-semibold text-zinc-900 text-center mb-2">{{ titulo }}</h3>
        <p v-if="mensaje" class="text-sm text-zinc-500 text-center mb-5 leading-relaxed whitespace-pre-line">{{ mensaje }}</p>
        <div class="flex gap-3">
          <button type="button" class="flex-1 h-10 px-4 text-sm font-medium text-zinc-700 bg-white border border-zinc-300 rounded-lg hover:bg-zinc-50"
                  @click="cancelar">{{ etiquetaCancelar }}</button>
          <button type="button" class="flex-1 h-10 px-4 text-sm font-medium text-white rounded-lg" :class="v.boton"
                  @click="confirmar">{{ etiquetaConfirmar }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { ExclamationTriangleIcon, CheckCircleIcon, InformationCircleIcon, TrashIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  titulo: { type: String, default: '¿Confirmar acción?' },
  mensaje: { type: String, default: '' },
  etiquetaConfirmar: { type: String, default: 'Confirmar' },
  etiquetaCancelar: { type: String, default: 'Cancelar' },
  variante: { type: String, default: 'aviso' }, // primaria | aviso | critica | exito
})
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const VARIANTES = {
  primaria: { fondo: 'bg-primary-100', color: 'text-primary-600', boton: 'bg-primary-600 hover:bg-primary-700', icon: InformationCircleIcon },
  aviso:    { fondo: 'bg-amber-100',   color: 'text-amber-600',   boton: 'bg-amber-500 hover:bg-amber-600',     icon: ExclamationTriangleIcon },
  critica:  { fondo: 'bg-red-100',     color: 'text-red-600',     boton: 'bg-red-600 hover:bg-red-700',         icon: TrashIcon },
  exito:    { fondo: 'bg-emerald-100', color: 'text-emerald-600', boton: 'bg-emerald-600 hover:bg-emerald-700', icon: CheckCircleIcon },
}
const v = computed(() => VARIANTES[props.variante] || VARIANTES.aviso)

function confirmar() { emit('confirm'); emit('update:modelValue', false) }
function cancelar() { emit('cancel'); emit('update:modelValue', false) }
</script>
