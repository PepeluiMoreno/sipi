import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Transmisiones usando Strawchemy
 */

export const LISTAR = gql`
  query ListarTransmisiones($filter: TransmisionFilterInput, $offset: Int = 0, $limit: Int = 50) {
    transmisiones(filter: $filter, offset: $offset, limit: $limit) {
      id
      inmuebleId
      inmueble {
        id
        nombre
      }
      transmitenteId
      adquirienteId
      notariaId
      tipoTransmisionId
      tipoTransmision {
        id
        nombre
      }
      fechaTransmision
      descripcion
      precioVenta
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerTransmision($filter: TransmisionFilterInput!) {
    transmisiones(filter: $filter, limit: 1) {
      id
      inmuebleId
      inmueble {
        id
        nombre
        direccionNormalizada
      }
      transmitenteId
      transmitente {
        id
        nombre
      }
      adquirienteId
      adquiriente {
        id
        nombre
      }
      notariaId
      notaria {
        id
        nombre
      }
      registroPropiedadId
      registroPropiedad {
        id
        nombre
      }
      tipoTransmisionId
      tipoTransmision {
        id
        nombre
      }
      fechaTransmision
      descripcion
      precioVenta
      
      # Si Strawchemy soporta estas relaciones
      documento {
        id
        titulo
      }
    }
  }
`

export const CREAR = gql`
  mutation CrearTransmision($data: TransmisionCreateInput!) {
    createTransmision(data: $data) {
      id
      fechaTransmision
      precioVenta
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTransmision($data: TransmisionUpdateInput!) {
    updateTransmision(data: $data) {
      id
      fechaTransmision
      precioVenta
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