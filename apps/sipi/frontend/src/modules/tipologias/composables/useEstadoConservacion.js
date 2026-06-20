import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/estadoConservacionQueries.js'

export function useEstadoConservacion() {
  return useTipologiaBaseStrawchemy('estadosConservacion', queries)
}