import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Registros de Propiedad usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarRegistrosPropiedad(
    $filter: RegistroPropiedadFilter
    $offset: Int = 0
    $limit: Int = 50
  ) {
    registrosPropiedad(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      nombreRegistrador
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
      titulares {
        id
        nombre
        apellidos
        fechaInicio
        fechaFin
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerRegistroPropiedad(
    $filter: RegistroPropiedadFilter!
  ) {
    registrosPropiedad(filter: $filter, limit: 1) {
      id
      nombre
      nombreRegistrador
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
  query BuscarRegistrosPropiedad(
    $search: String!
    $limit: Int = 50
  ) {
    registrosPropiedad(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { nombreRegistrador: { ilike: $search } }
          { numeroIdentificacion: { contains: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      nombreRegistrador
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
  query ListarRegistrosPropiedadPorMunicipio(
    $municipioId: ID!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    registrosPropiedad(
      filter: { municipioId: { eq: $municipioId } }
      offset: $offset
      limit: $limit
    ) {
      id
      nombre
      nombreRegistrador
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
  mutation CrearRegistroPropiedad($data: RegistroPropiedadCreateInput!) {
    createRegistroPropiedad(data: $data) {
      id
      nombre
      nombreRegistrador
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
  mutation ActualizarRegistroPropiedad($data: RegistroPropiedadUpdateInput!) {
    updateRegistroPropiedad(data: $data) {
      id
      nombre
      nombreRegistrador
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
  mutation EliminarRegistroPropiedad($id: ID!) {
    deleteRegistrosPropiedad(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
