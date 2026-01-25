import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/notariaTitularQueries.js'

export function useNotariaTitular(notariaId) {
  const base = useAgenteBase('notariaTitulares', queries)

  const listar = async () => {
    return base.listar({ notariaId: { eq: notariaId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, notariaId })
  }

  return {
    ...base,
    titulares: base.items,
    titular: base.item,
    listar,
    crear
  }
}