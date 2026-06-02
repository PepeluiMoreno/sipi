import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Titulares de Administración con Strawchemy
 */

export const LISTAR = gql`
  query ListarAdministracionTitulares(
    $filter: AdministracionTitularFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    administracionTitulares(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      administracion {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerAdministracionTitular(
    $filter: AdministracionTitularFilterInput!
  ) {
    administracionTitulares(filter: $filter, limit: 1) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      administracion {
        id
        nombre
      }
      createdAt
      updatedAt
    }
  }
`

export const CREAR = gql`
  mutation CrearAdministracionTitular($data: AdministracionTitularCreateInput!) {
    createAdministracionTitular(data: $data) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      administracion {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarAdministracionTitular($data: AdministracionTitularUpdateInput!) {
    updateAdministracionTitular(data: $data) {
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
  mutation EliminarAdministracionTitular($id: ID!) {
    deleteAdministracionTitulares(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
