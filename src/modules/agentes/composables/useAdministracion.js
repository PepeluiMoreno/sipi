import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/administracionQueries.js'

/**
 * Composable para Administraciones adaptado a Strawchemy
 *
 * Delegamos a useAgenteBase que ya tiene toda la lógica necesaria
 * y además está correctamente configurado para usar Apollo Client
 */
export function useAdministracion() {
  // Delegar a useAgenteBase con las queries específicas de administraciones
  const base = useAgenteBase('administraciones', queries)

  /**
   * Listar por ámbito
   * @param {String} ambito - ESTATAL, AUTONOMICO, LOCAL, etc.
   */
  const listarPorAmbito = async (ambito) => {
    return base.listar({ ambito: { eq: ambito } })
  }

  /**
   * Listar por municipio
   * @param {String} municipioId - UUID del municipio
   */
  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    // Métodos específicos
    listarPorAmbito,
    listarPorMunicipio
  }
}