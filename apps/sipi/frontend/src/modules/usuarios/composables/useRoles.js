import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/rolQueries.js'

export function useRoles() {
  const base = useAgenteBase('roles', queries)

  return {
    ...base,
    roles: base.items,
    rol: base.item
  }
}