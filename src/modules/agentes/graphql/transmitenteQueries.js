import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Transmitentes usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarTransmitentes(
    $filter: TransmitenteFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    transmitentes(filter: $filter, offset: $offset, limit: $limit) {
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
  query ObtenerTransmitente(
    $filter: TransmitenteFilterInput!
  ) {
    transmitentes(filter: $filter, limit: 1) {
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
  query BuscarTransmitentes(
    $search: String!
    $limit: Int = 50
  ) {
    transmitentes(
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
  mutation CrearTransmitente($data: TransmitenteCreateInput!) {
    createTransmitente(data: $data) {
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
  mutation ActualizarTransmitente($data: TransmitenteUpdateInput!) {
    updateTransmitente(data: $data) {
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
  mutation EliminarTransmitente($id: ID!) {
    deleteTransmitentes(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
