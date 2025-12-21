import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/rolTecnicoQueries.js'

export function useRolTecnico() {
  return useCatalogoBaseStrawchemy('rolesTecnicos', queries)
}