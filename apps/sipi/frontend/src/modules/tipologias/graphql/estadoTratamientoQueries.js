import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarEstadosTratamiento($filter: EstadoTratamientoFilterInput, $offset: Int = 0, $limit: Int = 50) {
    estadosTratamiento(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerEstadoTratamiento($filter: EstadoTratamientoFilterInput!) {
    estadosTratamiento(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearEstadoTratamiento($data: EstadoTratamientoCreateInput!) {
    createEstadoTratamiento(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarEstadoTratamiento($data: EstadoTratamientoUpdateInput!) {
    updateEstadoTratamiento(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarEstadoTratamiento($id: ID!) {
    deleteEstadosTratamiento(filter: { id: { eq: $id } }) {
      id
    }
  }
`