import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoMimeDocumentoQueries.js'

export function useTipoMimeDocumento() {
  return useTipologiaBaseStrawchemy('tiposMimeDocumento', queries)
}