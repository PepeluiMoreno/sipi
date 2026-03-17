import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/adquirienteQueries.js'

export function useAdquiriente() {
  const base = useAgenteBase('adquirientes', queries)

  const adquirientes = computed(() => base.items.value)
  const adquiriente = computed(() => base.item.value)

  return {
    ...base,
    adquirientes,
    adquiriente
  }
}