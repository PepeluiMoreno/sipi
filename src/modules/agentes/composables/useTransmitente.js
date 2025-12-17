import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/transmitenteQueries.strawchemy'

export function useTransmitente() {
  const base = useAgenteBaseStrawchemy('transmitentes', queries)

  return {
    ...base
  }
}