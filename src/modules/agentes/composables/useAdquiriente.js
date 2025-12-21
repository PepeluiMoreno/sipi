import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/adquirienteQueries.js'

export function useAdquiriente() {
  const base = useAgenteBaseStrawchemy('adquirientes', queries)

  const adquirientes = computed(() => base.items.value)
  const adquiriente = computed(() => base.item.value)

  return {
    ...base,
    adquirientes,
    adquiriente
  }
}