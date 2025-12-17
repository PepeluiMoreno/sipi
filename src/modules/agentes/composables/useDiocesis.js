import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/diocesisQueries.strawchemy'

export function useDiocesis() {
  const base = useAgenteBaseStrawchemy('diocesis', queries)

  // Alias para mantener compatibilidad con código existente
  const diocesis = computed(() => base.items.value)
  const diocesisActual = computed(() => base.item.value)

  return {
    // Estado con nombres personalizados
    diocesis,
    diocesis: diocesisActual, // Mantenemos la duplicación del original
    loading: base.loading,
    error: base.error,
    pagination: computed(() => ({
      page: 1,
      pageSize: base.limit.value,
      total: base.totalCargados.value
    })),

    // Métodos del base
    listar: base.listar,
    obtener: base.obtener,
    crear: base.crear,
    actualizar: base.actualizar,
    eliminar: base.eliminar,
    buscar: base.buscar,
    cargarMas: base.cargarMas,
    reset: base.reset
  }
}
