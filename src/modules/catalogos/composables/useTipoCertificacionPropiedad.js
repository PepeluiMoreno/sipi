import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/tipoCertificacionPropiedadQueries.js'

export function useTipoCertificacionPropiedad() {
  return useCatalogoBaseStrawchemy('tiposCertificacionPropiedad', queries)
}