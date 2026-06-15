import { useAgenteBase } from './useAgenteBase'
import * as queries from '../graphql/entidadReligiosaQueries.js'

/**
 * Composable para Entidades Religiosas — delega en useAgenteBase con sus queries reales.
 */
export function useEntidadReligiosa() {
  return useAgenteBase('entidadesReligiosas', queries)
}
