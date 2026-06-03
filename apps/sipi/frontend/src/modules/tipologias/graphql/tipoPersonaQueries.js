import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposPersona($filter: TipoPersonaFilterInput, $offset: Int = 0, $limit: Int = 50) {
    tiposPersona(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoPersona($filter: TipoPersonaFilterInput!) {
    tiposPersona(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoPersona($data: TipoPersonaCreateInput!) {
    createTipoPersona(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoPersona($data: TipoPersonaUpdateInput!) {
    updateTipoPersona(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoPersona($id: ID!) {
    deleteTiposPersona(filter: { id: { eq: $id } }) {
      id
    }
  }
`