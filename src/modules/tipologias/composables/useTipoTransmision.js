import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoTransmisionQueries.js'

export function useTipoTransmision() {
  return useTipologiaBaseStrawchemy('tiposTransmision', queries)
}