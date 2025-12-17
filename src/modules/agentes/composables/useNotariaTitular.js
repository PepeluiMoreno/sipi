import { toRefs } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/notariaTitularQueries.strawchemy'

export function useNotariaTitular(notariaId) {
  const base = useAgenteBaseStrawchemy('notariaTitulares', {
    LISTAR: queries.LISTAR,
    OBTENER: queries.OBTENER,
    CREAR: queries.CREAR,
    ACTUALIZAR: queries.ACTUALIZAR,
    ELIMINAR: queries.ELIMINAR
  })

  const { items, item } = toRefs(base) // or just use base.items via alias

  /**
   * Listar titulares de esta notaría
   */
  const listar = async () => {
    // Forzamos el filtro por notariaId
    return base.listar({
      notariaId: { eq: notariaId }
    })
  }

  /**
   * Crear titular para esta notaría
   */
  const crear = async (inputData) => {
    // Inyectar notariaId
    return base.crear({
      ...inputData,
      notariaId
    })
  }

  return {
    ...base,
    // Alias common names
    titulares: base.items,
    titular: base.item,

    listar,
    crear
  }
}