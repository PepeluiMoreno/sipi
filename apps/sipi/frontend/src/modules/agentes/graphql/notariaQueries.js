import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Notarias usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarNotarias($search: String, $offset: Int = 0, $limit: Int = 50) {
    notarias(search: $search, offset: $offset, limit: $limit) {
      items {
        id codigoOficial nombre emailCorporativo emailPersonal telefono telefonoMovil
        nombreVia numero codigoPostal comunidadAutonomaId provinciaId municipioId
      }
      total
    }
  }
`

export const OBTENER = gql`
  query ObtenerNotaria(
    $filter: NotariaFilterInput!
  ) {
    notarias(filter: $filter, limit: 1) {
      id
      nombre
      nombreNotario
      numeroIdentificacion
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
      colegioProfesional {
        id
        nombre
      }
      titulares {
        id
        nombre
        apellidos
        numeroIdentificacion
        fechaInicio
        fechaFin
      }
      createdAt
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarNotarias(
    $search: String!
    $limit: Int = 50
  ) {
    notarias(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { nombreNotario: { ilike: $search } }
          { numeroIdentificacion: { contains: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      nombreNotario
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
  query ListarNotariasPorMunicipio(
    $municipioId: ID!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    notarias(
      filter: { municipioId: { eq: $municipioId } }
      offset: $offset
      limit: $limit
    ) {
      id
      nombre
      nombreNotario
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
  mutation CrearNotaria($data: NotariaCreateInput!) {
    createNotaria(data: $data) {
      id
      nombre
      nombreNotario
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
  mutation ActualizarNotaria($data: NotariaUpdateInput!) {
    updateNotaria(data: $data) {
      id
      nombre
      nombreNotario
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
  mutation EliminarNotaria($id: ID!) {
    deleteNotarias(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
