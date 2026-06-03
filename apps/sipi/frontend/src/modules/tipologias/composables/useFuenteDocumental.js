import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/fuenteDocumentalQueries.js'

export function useFuenteDocumental() {
  return useTipologiaBaseStrawchemy('fuentesDocumentales', queries)
}