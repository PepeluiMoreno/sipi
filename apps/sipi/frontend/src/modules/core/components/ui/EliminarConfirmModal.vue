<!--
  EliminarConfirmModal.vue — confirmación de borrado (modal, compartida por todas las vistas).
  Por defecto SOFT-DELETE (a la papelera). Checkbox para borrado permanente.
  Explica la implicación de integridad de cada opción. Emite confirm(permanente: boolean).
-->
<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-zinc-900/40" @click="cancelar" />
      <div class="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <div class="flex items-center justify-center w-12 h-12 rounded-full mx-auto mb-4"
             :class="permanente ? 'bg-red-100' : 'bg-amber-100'">
          <TrashIcon class="w-6 h-6" :class="permanente ? 'text-red-600' : 'text-amber-600'" />
        </div>
        <h3 class="text-base font-semibold text-zinc-900 text-center">
          {{ permanente ? 'Eliminar permanentemente' : 'Enviar a la papelera' }}
        </h3>
        <p v-if="nombre" class="text-sm text-zinc-600 text-center mt-1 mb-4">«{{ nombre }}»</p>
        <div v-else class="mb-4"></div>

        <!-- Implicación de integridad según la opción -->
        <div class="rounded-lg p-3 text-xs leading-relaxed mb-4"
             :class="permanente ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-800'">
          <template v-if="!permanente">
            <b>Borrado lógico (soft-delete).</b> El registro se marca como eliminado
            (<code>deleted_at</code>) y desaparece de los listados, pero <b>permanece en la base de
            datos</b> con sus relaciones intactas: lo que apunte a él sigue resolviendo. Es
            <b>recuperable</b> desde la Papelera y no rompe integridad referencial.
          </template>
          <template v-else>
            <b>Borrado permanente.</b> Elimina la fila físicamente: <b>irreversible</b> y no pasa por la
            Papelera. Puede <b>fallar o arrastrar datos relacionados</b> (claves foráneas en cascada).
            Úsalo solo si estás seguro de que ningún otro registro depende de este.
          </template>
        </div>

        <label class="flex items-center gap-2 text-sm text-zinc-700 mb-5">
          <input type="checkbox" v-model="permanente"
                 class="rounded border-zinc-300 text-red-600 focus:ring-red-500" />
          Borrado permanente (no recuperable)
        </label>

        <div class="flex gap-3">
          <button type="button" @click="cancelar"
                  class="flex-1 h-10 px-4 text-sm font-medium text-zinc-700 bg-white border border-zinc-300 rounded-lg hover:bg-zinc-50">
            Cancelar
          </button>
          <button type="button" @click="confirmar"
                  class="flex-1 h-10 px-4 text-sm font-medium text-white rounded-lg"
                  :class="permanente ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-500 hover:bg-amber-600'">
            {{ permanente ? 'Eliminar permanentemente' : 'Enviar a la papelera' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { TrashIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  nombre: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const permanente = ref(false)
watch(() => props.modelValue, (v) => { if (v) permanente.value = false }) // reset al abrir

function confirmar() { emit('confirm', permanente.value); emit('update:modelValue', false) }
function cancelar() { emit('cancel'); emit('update:modelValue', false) }
</script>
