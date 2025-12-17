import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/registroPropiedadQueries.strawchemy'

export function useRegistroPropiedad() {
  const base = useAgenteBaseStrawchemy('registrosPropiedad', queries)

  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    listarPorMunicipio
  }
}
