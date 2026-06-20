import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Colegios Profesionales usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarColegiosProfesionales(
    $search: String
    $offset: Int = 0
    $limit: Int = 500
    $filters: [FilterInput!]
  ) {
    colegiosProfesionales(search: $search, offset: $offset, limit: $limit, filters: $filters) {
      items {
        id
        nombre
        nombreResponsable
        email
        telefono
        direccion
        codigoPostal
        municipioSede { id nombre }
      }
      total
    }
  }
`

export const OBTENER = gql`
  query ObtenerColegioProfesional(
    $filter: ColegioProfesionalFilterInput!
  ) {
    colegiosProfesionales(filter: $filter, limit: 1) {
      id
      nombre
      nombreResponsable
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
        codigoIne
        provincia {
          id
          nombre
        }
      }
      createdAt
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarColegiosProfesionales(
    $search: String!
    $limit: Int = 50
  ) {
    colegiosProfesionales(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { nombreResponsable: { ilike: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      nombreResponsable
      email
      telefono
      municipio {
        id
        nombre
      }
    }
  }
`

export const LISTAR_POR_MUNICIPIO = gql`
  query ListarColegiosProfesionalesPorMunicipio(
    $municipioId: ID!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    colegiosProfesionales(
      filter: { municipioId: { eq: $municipioId } }
      offset: $offset
      limit: $limit
    ) {
      id
      nombre
      nombreResponsable
      direccion
      telefono
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
  mutation CrearColegioProfesional($data: ColegioProfesionalCreateInput!) {
    createColegioProfesional(data: $data) {
      id
      nombre
      nombreResponsable
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
  mutation ActualizarColegioProfesional($data: ColegioProfesionalUpdateInput!) {
    updateColegioProfesional(data: $data) {
      id
      nombre
      nombreResponsable
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
  mutation EliminarColegioProfesional($id: ID!) {
    deleteColegioProfesional(id: $id)
  }
`
