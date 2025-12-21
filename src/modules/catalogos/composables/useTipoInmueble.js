import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoInmuebleQueries.js'

export function useTipoInmueble() {
  return useCatalogoBaseStrawchemy('tiposInmueble', queries)
}