import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoLicenciaQueries.js'

export function useTipoLicencia() {
  return useTipologiaBaseStrawchemy('tiposLicencia', queries)
}