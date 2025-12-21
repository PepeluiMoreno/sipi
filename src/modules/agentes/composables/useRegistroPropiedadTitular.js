import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/registroPropiedadTitularQueries.js'

export function useRegistroPropiedadTitular(registroPropiedadId) {
  const base = useAgenteBaseStrawchemy('registroPropiedadTitulares', queries)

  const listar = async () => {
    return base.listar({ registroPropiedadId: { eq: registroPropiedadId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, registroPropiedadId })
  }

  return {
    ...base,
    titulares: base.items,
    titular: base.item,
    listar,
    crear
  }
}