import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/transmisionQueries.js'

export function useTransmision() {
  const base = useAgenteBase('transmisiones', queries)

  return {
    ...base,
    transmisiones: base.items,
    transmision: base.item
  }
}