import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Adquirientes usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarAdquirientes(
    $filter: AdquirienteFilter
    $offset: Int = 0
    $limit: Int = 50
  ) {
    adquirientes(filter: $filter, offset: $offset, limit: $limit) {
      id
      tipoIdentificacion
      numeroIdentificacion
      nombre
      apellidos
      razonSocial
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
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerAdquiriente(
    $filter: AdquirienteFilter!
  ) {
    adquirientes(filter: $filter, limit: 1) {
      id
      tipoIdentificacion
      numeroIdentificacion
      nombre
      apellidos
      razonSocial
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
        codigoIne
      }
      createdAt
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarAdquirientes(
    $search: String!
    $limit: Int = 50
  ) {
    adquirientes(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { apellidos: { ilike: $search } }
          { razonSocial: { ilike: $search } }
          { numeroIdentificacion: { contains: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      apellidos
      razonSocial
      numeroIdentificacion
      email
      telefono
    }
  }
`

// ========================================
// MUTATIONS
// ========================================

export const CREAR = gql`
  mutation CrearAdquiriente($data: AdquirienteCreateInput!) {
    createAdquiriente(data: $data) {
      id
      nombre
      apellidos
      razonSocial
      numeroIdentificacion
      email
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarAdquiriente($data: AdquirienteUpdateInput!) {
    updateAdquiriente(data: $data) {
      id
      nombre
      apellidos
      razonSocial
      numeroIdentificacion
      email
      telefono
      direccion
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarAdquiriente($id: ID!) {
    deleteAdquirientes(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
