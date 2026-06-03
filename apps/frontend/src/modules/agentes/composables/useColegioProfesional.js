import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/colegioProfesionalQueries.js'

export function useColegioProfesional() {
  const base = useAgenteBase('colegiosProfesionales', queries)

  const colegiosProfesionales = computed(() => base.items.value)
  const colegioProfesional = computed(() => base.item.value)

  return {
    ...base,
    colegiosProfesionales,
    colegioProfesional
  }
}