import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/agenciaInmobiliariaQueries.js'

export function useAgenciaInmobiliaria() {
  const base = useAgenteBase('agenciasInmobiliarias', queries)

  const agenciasInmobiliarias = computed(() => base.items.value)
  const agenciaInmobiliaria = computed(() => base.item.value)

  return {
    ...base,
    agenciasInmobiliarias,
    agenciaInmobiliaria
  }
}