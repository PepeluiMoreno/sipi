import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/colegioProfesionalQueries.strawchemy'

export function useColegioProfesional() {
  const base = useAgenteBaseStrawchemy('colegiosProfesionales', queries)

  return {
    ...base
  }
}