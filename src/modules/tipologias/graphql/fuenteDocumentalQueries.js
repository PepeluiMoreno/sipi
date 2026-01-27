import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarFuentesDocumentales($filter: FuenteDocumentalFilterInput, $offset: Int = 0, $limit: Int = 50) {
    fuentesDocumentales(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
    }
  }
`

export const OBTENER = gql`
  query ObtenerFuenteDocumental($filter: FuenteDocumentalFilterInput!) {
    fuentesDocumentales(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
    }
  }
`

export const CREAR = gql`
  mutation CrearFuenteDocumental($data: FuenteDocumentalCreateInput!) {
    createFuenteDocumental(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarFuenteDocumental($data: FuenteDocumentalUpdateInput!) {
    updateFuenteDocumental(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarFuenteDocumental($id: ID!) {
    deleteFuentesDocumentales(filter: { id: { eq: $id } }) {
      id
    }
  }
`