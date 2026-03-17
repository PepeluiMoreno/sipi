import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/rolTecnicoQueries.js'

export function useRolTecnico() {
  return useTipologiaBaseStrawchemy('rolesTecnicos', queries)
}