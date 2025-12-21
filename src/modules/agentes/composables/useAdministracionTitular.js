import { toRefs } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/administracionTitularQueries.js'

export function useAdministracionTitular(administracionId) {
  const base = useAgenteBaseStrawchemy('administracionTitulares', queries)

  // Desestructurar para uso local si hace falta, pero mantenemos base

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