import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposLicencia($filter: TipoLicenciaFilterInput, $offset: Int = 0, $limit: Int = 50) {
    tiposLicencia(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoLicencia($filter: TipoLicenciaFilterInput!) {
    tiposLicencia(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoLicencia($data: TipoLicenciaCreateInput!) {
    createTipoLicencia(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoLicencia($data: TipoLicenciaUpdateInput!) {
    updateTipoLicencia(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoLicencia($id: ID!) {
    deleteTiposLicencia(filter: { id: { eq: $id } }) {
      id
    }
  }
`