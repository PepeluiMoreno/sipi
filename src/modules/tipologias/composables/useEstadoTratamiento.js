import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/estadoTratamientoQueries.js'

export function useEstadoTratamiento() {
  // 'estadosTratamiento' plural assumed
  return useTipologiaBaseStrawchemy('estadosTratamiento', queries)
}