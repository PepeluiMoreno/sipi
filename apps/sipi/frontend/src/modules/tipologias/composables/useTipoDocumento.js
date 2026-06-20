import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoDocumentoQueries.js'

export function useTipoDocumento() {
  return useTipologiaBaseStrawchemy('tiposDocumento', queries)
}