import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/agenciaInmobiliariaQueries.js'

export function useAgenciaInmobiliaria() {
  const base = useAgenteBaseStrawchemy('agenciasInmobiliarias', queries)

  const agenciasInmobiliarias = computed(() => base.items.value)
  const agenciaInmobiliaria = computed(() => base.item.value)

  return {
    ...base,
    agenciasInmobiliarias,
    agenciaInmobiliaria
  }
}