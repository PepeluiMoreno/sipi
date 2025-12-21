import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Denominaciones usando Strawchemy
 */

export const LISTAR = gql`
  query ListarDenominaciones($filter: InmuebleDenominacionFilter, $offset: Int = 0, $limit: Int = 50) {
    inmuebleDenominaciones(filter: $filter, offset: $offset, limit: $limit) {
      id
      inmuebleId
      denominacion
      esPrincipal
      idioma
      fechaInicio
      fechaFin
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerDenominacion($filter: InmuebleDenominacionFilter!) {
    inmuebleDenominaciones(filter: $filter, limit: 1) {
      id
      inmuebleId
      denominacion
      esPrincipal
      idioma
    }
  }
`

export const CREAR = gql`
  mutation CrearDenominacion($data: InmuebleDenominacionCreateInput!) {
    createInmuebleDenominacion(data: $data) {
      id
      denominacion
      esPrincipal
      idioma
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarDenominacion($data: InmuebleDenominacionUpdateInput!) {
    updateInmuebleDenominacion(data: $data) {
      id
      denominacion
      esPrincipal
      idioma
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarDenominacion($id: ID!) {
    deleteInmuebleDenominaciones(filter: { id: { eq: $id } }) {
      id
    }
  }
`