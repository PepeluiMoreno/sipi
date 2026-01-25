import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposDocumento($filter: TipoDocumentoFilter, $offset: Int = 0, $limit: Int = 50) {
    tiposDocumento(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoDocumento($filter: TipoDocumentoFilter!) {
    tiposDocumento(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoDocumento($data: TipoDocumentoCreateInput!) {
    createTipoDocumento(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoDocumento($data: TipoDocumentoUpdateInput!) {
    updateTipoDocumento(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoDocumento($id: ID!) {
    deleteTiposDocumento(filter: { id: { eq: $id } }) {
      id
    }
  }
`