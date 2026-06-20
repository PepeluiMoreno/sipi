import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/registroPropiedadQueries.js'

export function useRegistroPropiedad() {
  const base = useAgenteBase('registrosPropiedades', queries)

  const registrosPropiedad = computed(() => base.items.value)
  const registroPropiedad = computed(() => base.item.value)

  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    registrosPropiedad,
    registroPropiedad,
    listarPorMunicipio
  }
}
