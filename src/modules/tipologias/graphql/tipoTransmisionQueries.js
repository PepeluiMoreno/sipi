import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposTransmision($filter: TipoTransmisionFilter, $offset: Int = 0, $limit: Int = 50) {
    tiposTransmision(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoTransmision($filter: TipoTransmisionFilter!) {
    tiposTransmision(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoTransmision($data: TipoTransmisionCreateInput!) {
    createTipoTransmision(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoTransmision($data: TipoTransmisionUpdateInput!) {
    updateTipoTransmision(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoTransmision($id: ID!) {
    deleteTiposTransmision(filter: { id: { eq: $id } }) {
      id
    }
  }
`