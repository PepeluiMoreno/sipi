import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/colegioProfesionalQueries.js'

export function useColegioProfesional() {
  const base = useAgenteBaseStrawchemy('colegiosProfesionales', queries)

  const colegiosProfesionales = computed(() => base.items.value)
  const colegioProfesional = computed(() => base.item.value)

  return {
    ...base,
    colegiosProfesionales,
    colegioProfesional
  }
}