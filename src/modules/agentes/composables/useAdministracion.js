import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/administracionQueries.strawchemy'

export function useAdministracion() {
  const base = useAgenteBaseStrawchemy('administraciones', {
    LISTAR: queries.LISTAR_ADMINISTRACIONES,
    OBTENER: queries.OBTENER_ADMINISTRACION,
    BUSCAR: queries.BUSCAR_ADMINISTRACIONES,
    CREAR: queries.CREAR_ADMINISTRACION,
    ACTUALIZAR: queries.ACTUALIZAR_ADMINISTRACION,
    ELIMINAR: queries.ELIMINAR_ADMINISTRACION
  })

  /**
   * Listar por ámbito
   * @param {String} ambito - ESTATAL, AUTONOMICO, LOCAL, etc.
   */
  const listarPorAmbito = async (ambito) => {
    return base.listar({ ambito: { eq: ambito } })
  }

  /**
   * Listar por municipio (localidad)
   * @param {String} localidadId - UUID del municipio
   */
  const listarPorLocalidad = async (localidadId) => {
    return base.listar({ municipioId: { eq: localidadId } })
  }

  return {
    ...base,
    listarPorAmbito,
    listarPorLocalidad
  }
}