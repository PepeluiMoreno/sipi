import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Transmisiones usando Strawchemy
 * Entidad base: Transmision -> transmisiones
 */

export const LISTAR = gql`
  query ListarTransmisiones($filter: TransmisionFilterInput, $offset: Int = 0, $limit: Int = 50) {
    transmisiones(filter: $filter, offset: $offset, limit: $limit) {
      id
      inmuebleId
      tipoTransmision
      fechaTransmision
      transmitente
      adquirente
      estado
      observaciones
      createdAt
      updatedAt
      documento {
        id
        titulo
        tipo
      }
    }
  }
`

export const OBTENER = gql`
  query ObtenerTransmision($filter: TransmisionFilterInput!) {
    transmisiones(filter: $filter, limit: 1) {
      id
      inmuebleId
      tipoTransmision
      fechaTransmision
      transmitente
      adquirente
      estado
      observaciones
      createdAt
      updatedAt
      documento {
        id
        titulo
        tipo
        url
      }
      inmueble {
        id
        nombre
      }
    }
  }
`

export const CREAR = gql`
  mutation CrearTransmision($data: TransmisionCreateInput!) {
    createTransmision(data: $data) {
      id
      tipoTransmision
      fechaTransmision
      estado
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTransmision($data: TransmisionUpdateInput!) {
    updateTransmision(data: $data) {
      id
      tipoTransmision
      fechaTransmision
      estado
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTransmision($id: ID!) {
    deleteTransmisiones(filter: { id: { eq: $id } }) {
      id
    }
  }
`

export const GENERAR_CEDULA = gql`
  mutation GenerarCedulaTransmision($transmisionId: ID!) {
    generarCedulaTransmision(transmisionId: $transmisionId) {
      success
      message
    }
  }
`