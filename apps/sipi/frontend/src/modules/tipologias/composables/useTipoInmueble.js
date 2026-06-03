import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoInmuebleQueries.js'

export function useTipoInmueble() {
  return useTipologiaBaseStrawchemy('tiposInmueble', queries)
}