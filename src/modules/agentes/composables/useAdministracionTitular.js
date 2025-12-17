import { toRefs } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/administracionTitularQueries.strawchemy'

export function useAdministracionTitular(administracionId) {
  const base = useAgenteBaseStrawchemy('administracionTitulares', {
    LISTAR: queries.LISTAR,
    OBTENER: queries.OBTENER,
    CREAR: queries.CREAR,
    ACTUALIZAR: queries.ACTUALIZAR,
    ELIMINAR: queries.ELIMINAR
  })

  const { items, item } = toRefs(base) // or just use base.items via alias

  /**
   * Listar titulares de esta administración
   */
  const listar = async () => {
    // Forzamos el filtro por administracionId
    return base.listar({
      administracionId: { eq: administracionId }
    })
  }

  /**
   * Crear titular para esta administración
   */
  const crear = async (inputData) => {
    // Inyectar administracionId
    return base.crear({
      ...inputData,
      administracionId
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