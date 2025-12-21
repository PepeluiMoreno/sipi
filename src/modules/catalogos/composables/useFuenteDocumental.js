import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/fuenteDocumentalQueries.js'

export function useFuenteDocumental() {
  return useCatalogoBaseStrawchemy('fuentesDocumentales', queries)
}