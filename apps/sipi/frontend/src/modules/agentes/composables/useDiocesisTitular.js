import { computed } from 'vue'
import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/diocesisTitularQueries.js'

export function useDiocesisTitular(diocesisId) {
  const base = useAgenteBase('diocesisTitulares', queries)

  const listar = async () => {
    return base.listar({ diocesisId: { eq: diocesisId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, diocesisId })
  }

  return {
    ...base,
    titulares: base.items,
    titular: base.item,
    listar,
    crear
  }
}