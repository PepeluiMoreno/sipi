import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/notariaQueries.js'

/**
 * Composable para Notarías
 * Reutiliza la lógica base de Strawchemy
 */
export function useNotaria() {
  const base = useAgenteBase('notarias', queries)

  // Alias para mantener compatibilidad
  const notarias = computed(() => base.items.value)
  const notaria = computed(() => base.item.value)

  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    notarias,
    notaria,
    listarPorMunicipio
  }
}
