import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Diócesis usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarDiocesis(
    $filter: DiocesisFilter
    $offset: Int = 0
    $limit: Int = 50
  ) {
    diocesis(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      wikidataQid
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
        provincia {
          id
          nombre
        }
      }
      titulares {
        id
        nombre
        apellidos
        fechaInicio
        fechaFin
        cargo
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerDiocesis(
    $filter: DiocesisFilter!
  ) {
    diocesis(filter: $filter, limit: 1) {
      id
      nombre
      wikidataQid
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
        codigoIne
      }
      titulares {
        id
        nombre
        apellidos
        numeroIdentificacion
        fechaInicio
        fechaFin
        cargo
      }
      createdAt
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarDiocesis(
    $search: String!
    $limit: Int = 50
  ) {
    diocesis(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { wikidataQid: { contains: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      wikidataQid
      email
      municipio {
        id
        nombre
      }
    }
  }
`

// ========================================
// MUTATIONS
// ========================================

export const CREAR = gql`
  mutation CrearDiocesis($data: DiocesisCreateInput!) {
    createDiocesis(data: $data) {
      id
      nombre
      wikidataQid
      email
      telefono
      municipio {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarDiocesis($data: DiocesisUpdateInput!) {
    updateDiocesis(data: $data) {
      id
      nombre
      wikidataQid
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
      }
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarDiocesis($id: ID!) {
    deleteDiocesis(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
