import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/adquirienteQueries.strawchemy'

export function useAdquiriente() {
  const base = useAgenteBaseStrawchemy('adquirientes', queries)

  return {
    ...base
  }
}