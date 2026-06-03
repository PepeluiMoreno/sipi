import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoViaQueries.js'

export function useTipoVia() {
  return useTipologiaBaseStrawchemy('tiposVia', queries)
}