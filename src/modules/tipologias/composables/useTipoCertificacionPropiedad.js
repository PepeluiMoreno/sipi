import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/tipoCertificacionPropiedadQueries.js'

export function useTipoCertificacionPropiedad() {
  return useTipologiaBaseStrawchemy('tiposCertificacionPropiedad', queries)
}