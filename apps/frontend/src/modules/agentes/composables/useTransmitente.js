import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/transmitenteQueries.js'

export function useTransmitente() {
  const base = useAgenteBase('transmitentes', queries)

  const transmitentes = computed(() => base.items.value)
  const transmitente = computed(() => base.item.value)

  return {
    ...base,
    transmitentes,
    transmitente
  }
}