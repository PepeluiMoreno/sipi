import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoLicenciaQueries.js'

export function useTipoLicencia() {
  return useCatalogoBaseStrawchemy('tiposLicencia', queries)
}