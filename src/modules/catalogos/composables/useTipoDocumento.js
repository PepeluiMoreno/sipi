import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoDocumentoQueries.js'

export function useTipoDocumento() {
  return useCatalogoBaseStrawchemy('tiposDocumento', queries)
}