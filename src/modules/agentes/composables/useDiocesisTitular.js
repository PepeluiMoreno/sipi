import { toRefs } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/diocesisTitularQueries.strawchemy'

export function useDiocesisTitular(diocesisId) {
  const base = useAgenteBaseStrawchemy('diocesisTitulares', {
    LISTAR: queries.LISTAR,
    OBTENER: queries.OBTENER,
    CREAR: queries.CREAR,
    ACTUALIZAR: queries.ACTUALIZAR,
    ELIMINAR: queries.ELIMINAR
  })

  const { items, item } = toRefs(base) // or just use base.items via alias

  /**
   * Listar titulares de esta diócesis
   */
  const listar = async () => {
    // Forzamos el filtro por diocesisId
    return base.listar({
      diocesisId: { eq: diocesisId }
    })
  }

  /**
   * Crear titular para esta diócesis
   */
  const crear = async (inputData) => {
    // Inyectar diocesisId
    return base.crear({
      ...inputData,
      diocesisId
    })
  }

  return {
    ...base,
    // Alias para compatibilidad con componentes existentes
    titulares: base.items,
    titular: base.item,

    // Overrides
    listar,
    crear
  }
}