import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoPersonaQueries.js'

export function useTipoPersona() {
  return useTipologiaBaseStrawchemy('tiposPersona', queries)
}