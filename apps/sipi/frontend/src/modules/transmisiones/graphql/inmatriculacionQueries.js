import { gql } from '@apollo/client/core'

export const OBTENER_INMATRICULACION = gql`
  query ObtenerInmatriculacion($inmuebleId: ID!) {
    inmatriculacion(inmuebleId: $inmuebleId) {
      item {
        id
        inmuebleId
        registroPropiedadId
        registroPropiedad {
          id
          nombre
          localidad {
            id
            nombre
          }
        }
        tipoCertificacionPropiedadId
        tipoCertificacionPropiedad {
          id
          nombre
        }
        fecha
        createdAt
        updatedAt
      }
    }
  }
`

export const CREAR_INMATRICULACION = gql`
  mutation CrearInmatriculacion($inmuebleId: ID!, $input: InmatriculacionInput!) {
    crearInmatriculacion(inmuebleId: $inmuebleId, input: $input) {
      success
      item {
        id
        inmuebleId
        fecha
      }
      message
    }
  }
`

export const ACTUALIZAR_INMATRICULACION = gql`
  mutation ActualizarInmatriculacion($inmuebleId: ID!, $input: InmatriculacionInput!) {
    actualizarInmatriculacion(inmuebleId: $inmuebleId, input: $input) {
      success
      item {
        id
        inmuebleId
        fecha
      }
      message
    }
  }
`

export const ELIMINAR_INMATRICULACION = gql`
  mutation EliminarInmatriculacion($inmuebleId: ID!) {
    eliminarInmatriculacion(inmuebleId: $inmuebleId) {
      success
      message
    }
  }
`