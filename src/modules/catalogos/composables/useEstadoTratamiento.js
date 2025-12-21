import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/estadoTratamientoQueries.js'

export function useEstadoTratamiento() {
  // 'estadosTratamiento' plural assumed
  return useCatalogoBaseStrawchemy('estadosTratamiento', queries)
}