import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoPersonaQueries.js'

export function useTipoPersona() {
  return useCatalogoBaseStrawchemy('tiposPersona', queries)
}