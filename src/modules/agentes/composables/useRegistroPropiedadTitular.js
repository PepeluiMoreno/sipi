import { toRefs } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/registroPropiedadTitularQueries.strawchemy'

export function useRegistroPropiedadTitular(registroPropiedadId) {
  const base = useAgenteBaseStrawchemy('registroPropiedadTitulares', {
    LISTAR: queries.LISTAR,
    OBTENER: queries.OBTENER,
    CREAR: queries.CREAR,
    ACTUALIZAR: queries.ACTUALIZAR,
    ELIMINAR: queries.ELIMINAR
  })

  /**
   * Listar titulares de este registro
   */
  const listar = async () => {
    return base.listar({
      registroPropiedadId: { eq: registroPropiedadId }
    })
  }

  /**
   * Crear titular para este registro
   */
  const crear = async (inputData) => {
    return base.crear({
      ...inputData,
      registroPropiedadId
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