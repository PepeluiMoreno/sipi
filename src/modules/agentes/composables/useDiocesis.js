import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/diocesisQueries.js'

export function useDiocesis() {
  const base = useAgenteBaseStrawchemy('diocesis', queries)

  const diocesis = computed(() => base.items.value)
  const item = computed(() => base.item.value) // diocesis singular is same

  return {
    ...base,
    diocesis,
    diocesisItem: item // Alias to avoid conflict if needed, though 'item' is standard
  }
}
