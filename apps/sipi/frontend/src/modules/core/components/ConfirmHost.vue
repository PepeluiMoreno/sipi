<!-- ConfirmHost.vue — monta el modal de confirmación global (úsalo una vez en App.vue) -->
<template>
  <ConfirmActionModal
    v-model="_confirmState.visible"
    :titulo="_confirmState.titulo"
    :mensaje="_confirmState.mensaje"
    :variante="_confirmState.variante"
    :etiqueta-confirmar="_confirmState.etiquetaConfirmar"
    :etiqueta-cancelar="_confirmState.etiquetaCancelar"
    @confirm="_resolveConfirm(true)"
    @cancel="_resolveConfirm(false)"
  />
</template>

<script setup>
import ConfirmActionModal from './ConfirmActionModal.vue'
import { _confirmState, _resolveConfirm } from '@/composables/useConfirm'
</script>
