import { gql } from '@apollo/client/core'

/**
 * STUB / DEPRECADO. «Actuación» se renombró a «Intervención» en el modelo
 * (sipi_core.modules.intervenciones). Este fichero resuelve el import del
 * composable `useInmuebleActuaciones` (que no se usa actualmente).
 * Usar las queries de intervenciones cuando se implemente la UI.
 */
export const LISTAR = gql`query { __typename }`
export const OBTENER = gql`query { __typename }`
export const CREAR = gql`mutation { __typename }`
export const ACTUALIZAR = gql`mutation { __typename }`
export const ELIMINAR = gql`mutation { __typename }`
