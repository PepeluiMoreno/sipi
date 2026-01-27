import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposMimeDocumento($filter: TipoMimeDocumentoFilterInput, $offset: Int = 0, $limit: Int = 50) {
    tiposMimeDocumento(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoMimeDocumento($filter: TipoMimeDocumentoFilterInput!) {
    tiposMimeDocumento(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoMimeDocumento($data: TipoMimeDocumentoCreateInput!) {
    createTipoMimeDocumento(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoMimeDocumento($data: TipoMimeDocumentoUpdateInput!) {
    updateTipoMimeDocumento(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoMimeDocumento($id: ID!) {
    deleteTiposMimeDocumento(filter: { id: { eq: $id } }) {
      id
    }
  }
`