import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Titulares de Notaria con Strawchemy
 */

export const LISTAR = gql`
  query ListarNotariaTitulares(
    $filter: NotariaTitularFilter
    $offset: Int = 0
    $limit: Int = 50
  ) {
    notariaTitulares(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      notaria {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerNotariaTitular(
    $filter: NotariaTitularFilter!
  ) {
    notariaTitulares(filter: $filter, limit: 1) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      notaria {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const CREAR = gql`
  mutation CrearNotariaTitular($data: NotariaTitularCreateInput!) {
    createNotariaTitular(data: $data) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      notaria {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarNotariaTitular($data: NotariaTitularUpdateInput!) {
    updateNotariaTitular(data: $data) {
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
  mutation EliminarNotariaTitular($id: ID!) {
    deleteNotariaTitulares(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
