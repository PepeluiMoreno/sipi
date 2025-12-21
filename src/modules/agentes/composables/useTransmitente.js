import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/transmitenteQueries.js'

export function useTransmitente() {
  const base = useAgenteBaseStrawchemy('transmitentes', queries)

  const transmitentes = computed(() => base.items.value)
  const transmitente = computed(() => base.item.value)

  return {
    ...base,
    transmitentes,
    transmitente
  }
}