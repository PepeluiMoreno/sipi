import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Agencias Inmobiliarias usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarAgenciasInmobiliarias(
    $filter: AgenciaInmobiliariaFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    agenciasInmobiliarias(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      nombreResponsable
      numeroIdentificacion
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
          comunidadAutonoma {
            id
            nombre
          }
        }
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerAgenciaInmobiliaria(
    $filter: AgenciaInmobiliariaFilterInput!
  ) {
    agenciasInmobiliarias(filter: $filter, limit: 1) {
      id
      nombre
      nombreResponsable
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
      createdAt
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarAgenciasInmobiliarias(
    $search: String!
    $limit: Int = 50
  ) {
    agenciasInmobiliarias(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { nombreResponsable: { ilike: $search } }
          { numeroIdentificacion: { contains: $search } }
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
  query ListarAgenciasInmobiliariasPorMunicipio(
    $municipioId: ID!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    agenciasInmobiliarias(
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
  mutation CrearAgenciaInmobiliaria($data: AgenciaInmobiliariaCreateInput!) {
    createAgenciaInmobiliaria(data: $data) {
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
  mutation ActualizarAgenciaInmobiliaria($data: AgenciaInmobiliariaUpdateInput!) {
    updateAgenciaInmobiliaria(data: $data) {
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
  mutation EliminarAgenciaInmobiliaria($id: ID!) {
    deleteAgenciasInmobiliarias(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
