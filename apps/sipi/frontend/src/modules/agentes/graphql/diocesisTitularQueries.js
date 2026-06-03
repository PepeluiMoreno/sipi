import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Titulares de Diócesis con Strawchemy
 */

export const LISTAR = gql`
  query ListarDiocesisTitulares(
    $filter: DiocesisTitularFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    diocesisTitulares(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      diocesis {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerDiocesisTitular(
    $filter: DiocesisTitularFilterInput!
  ) {
    diocesisTitulares(filter: $filter, limit: 1) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      diocesis {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const CREAR = gql`
  mutation CrearDiocesisTitular($data: DiocesisTitularCreateInput!) {
    createDiocesisTitular(data: $data) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      diocesis {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarDiocesisTitular($data: DiocesisTitularUpdateInput!) {
    updateDiocesisTitular(data: $data) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarDiocesisTitular($id: ID!) {
    deleteDiocesisTitulares(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
