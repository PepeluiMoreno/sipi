import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoViaQueries.js'

export function useTipoVia() {
  return useCatalogoBaseStrawchemy('tiposVia', queries)
}