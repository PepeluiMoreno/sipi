import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoMimeDocumentoQueries.js'

export function useTipoMimeDocumento() {
  return useCatalogoBaseStrawchemy('tiposMimeDocumento', queries)
}