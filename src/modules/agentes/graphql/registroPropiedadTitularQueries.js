import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Titulares de Registro de Propiedad con Strawchemy
 */

export const LISTAR = gql`
  query ListarRegistroPropiedadTitulares(
    $filter: RegistroPropiedadTitularFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    registroPropiedadTitulares(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      registroPropiedad {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerRegistroPropiedadTitular(
    $filter: RegistroPropiedadTitularFilterInput!
  ) {
    registroPropiedadTitulares(filter: $filter, limit: 1) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      registroPropiedad {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const CREAR = gql`
  mutation CrearRegistroPropiedadTitular($data: RegistroPropiedadTitularCreateInput!) {
    createRegistroPropiedadTitular(data: $data) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      registroPropiedad {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarRegistroPropiedadTitular($data: RegistroPropiedadTitularUpdateInput!) {
    updateRegistroPropiedadTitular(data: $data) {
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
  mutation EliminarRegistroPropiedadTitular($id: ID!) {
    deleteRegistroPropiedadTitulares(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
