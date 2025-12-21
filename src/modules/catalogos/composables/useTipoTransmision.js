import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoTransmisionQueries.js'

export function useTipoTransmision() {
  return useCatalogoBaseStrawchemy('tiposTransmision', queries)
}