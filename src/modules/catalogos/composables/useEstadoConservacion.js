import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/estadoConservacionQueries.js'

export function useEstadoConservacion() {
  return useCatalogoBaseStrawchemy('estadosConservacion', queries)
}