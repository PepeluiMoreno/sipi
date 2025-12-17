import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/notariaQueries.strawchemy'

export function useNotaria() {
  const base = useAgenteBaseStrawchemy('notarias', queries)

  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    listarPorMunicipio
  }
}
