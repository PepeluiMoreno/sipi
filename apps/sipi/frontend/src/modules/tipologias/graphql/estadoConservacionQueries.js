import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarEstadosConservacion($filter: EstadoConservacionFilterInput, $offset: Int = 0, $limit: Int = 50) {
    estadosConservacion(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerEstadoConservacion($filter: EstadoConservacionFilterInput!) {
    estadosConservacion(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearEstadoConservacion($data: EstadoConservacionCreateInput!) {
    createEstadoConservacion(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarEstadoConservacion($data: EstadoConservacionUpdateInput!) {
    updateEstadoConservacion(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarEstadoConservacion($id: ID!) {
    deleteEstadosConservacion(filter: { id: { eq: $id } }) {
      id
    }
  }
`