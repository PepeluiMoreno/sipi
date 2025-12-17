import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/agenciaInmobiliariaQueries.strawchemy'

export function useAgenciaInmobiliaria() {
  const base = useAgenteBaseStrawchemy('agenciasInmobiliarias', queries)

  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    listarPorMunicipio
  }
}