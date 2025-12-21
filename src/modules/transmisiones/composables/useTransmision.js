import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/transmisionQueries.js'

export function useTransmision() {
  const base = useAgenteBaseStrawchemy('transmisiones', queries)

  return {
    ...base,
    transmisiones: base.items,
    transmision: base.item
  }
}