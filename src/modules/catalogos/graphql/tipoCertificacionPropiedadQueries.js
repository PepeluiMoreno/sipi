import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarTiposCertificacionPropiedad($filter: TipoCertificacionPropiedadFilter, $offset: Int = 0, $limit: Int = 50) {
    tiposCertificacionPropiedad(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
    }
  }
`

export const OBTENER = gql`
  query ObtenerTipoCertificacionPropiedad($filter: TipoCertificacionPropiedadFilter!) {
    tiposCertificacionPropiedad(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
    }
  }
`

export const CREAR = gql`
  mutation CrearTipoCertificacionPropiedad($data: TipoCertificacionPropiedadCreateInput!) {
    createTipoCertificacionPropiedad(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTipoCertificacionPropiedad($data: TipoCertificacionPropiedadUpdateInput!) {
    updateTipoCertificacionPropiedad(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTipoCertificacionPropiedad($id: ID!) {
    deleteTiposCertificacionPropiedad(filter: { id: { eq: $id } }) {
      id
    }
  }
`