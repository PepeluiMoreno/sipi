import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposInmueble($filter: TipoInmuebleFilter, $offset: Int = 0, $limit: Int = 50) {
    tiposInmueble(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoInmueble($filter: TipoInmuebleFilter!) {
    tiposInmueble(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoInmueble($data: TipoInmuebleCreateInput!) {
    createTipoInmueble(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoInmueble($data: TipoInmuebleUpdateInput!) {
    updateTipoInmueble(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoInmueble($id: ID!) {
    deleteTiposInmueble(filter: { id: { eq: $id } }) {
      id
    }
  }
`