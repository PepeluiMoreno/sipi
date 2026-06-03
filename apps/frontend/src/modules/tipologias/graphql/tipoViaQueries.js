import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposVia($filter: TipoViaFilterInput, $offset: Int = 0, $limit: Int = 50) {
    tiposVia(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoVia($filter: TipoViaFilterInput!) {
    tiposVia(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoVia($data: TipoViaCreateInput!) {
    createTipoVia(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoVia($data: TipoViaUpdateInput!) {
    updateTipoVia(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoVia($id: ID!) {
    deleteTiposVia(filter: { id: { eq: $id } }) {
      id
    }
  }
`