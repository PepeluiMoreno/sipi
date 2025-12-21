import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/rolQueries.js'

export function useRoles() {
  const base = useAgenteBaseStrawchemy('roles', queries)

  return {
    ...base,
    roles: base.items,
    rol: base.item
  }
}