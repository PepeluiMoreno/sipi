import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/notariaQueries.js'

/**
 * Composable para Notarías
 * Reutiliza la lógica base de Strawchemy
 */
export function useNotaria() {
  const base = useAgenteBaseStrawchemy('notarias', queries)

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
