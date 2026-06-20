/**
 * useConfirm — sustituto de window.confirm() con un modal (estilo SIGA).
 * Requiere <ConfirmHost /> montado en App.vue.
 *
 *   const confirm = useConfirm()
 *   const ok = await confirm({ titulo: '¿Eliminar?', mensaje: '…', variante: 'critica', etiquetaConfirmar: 'Eliminar' })
 *   if (!ok) return
 */
import { ref } from 'vue'

const state = ref({
  visible: false,
  titulo: '¿Confirmar acción?',
  mensaje: '',
  variante: 'aviso',
  etiquetaConfirmar: 'Confirmar',
  etiquetaCancelar: 'Cancelar',
})

let _resolve = null

export const _confirmState = state

export function _resolveConfirm(ok) {
  if (_resolve) { _resolve(ok); _resolve = null }
  state.value.visible = false
}

export function useConfirm() {
  return function confirm(opts = {}) {
    state.value = {
      visible: true,
      titulo: opts.titulo ?? '¿Confirmar acción?',
      mensaje: opts.mensaje ?? '',
      variante: opts.variante ?? 'aviso',
      etiquetaConfirmar: opts.etiquetaConfirmar ?? 'Confirmar',
      etiquetaCancelar: opts.etiquetaCancelar ?? 'Cancelar',
    }
    return new Promise((resolve) => { _resolve = resolve })
  }
}
