import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Documentos usando Strawchemy
 * Entidad base: Documento -> documentos
 */

export const LISTAR = gql`
  query ListarDocumentos($filter: DocumentoFilterInput, $offset: Int = 0, $limit: Int = 50) {
    documentos(filter: $filter, offset: $offset, limit: $limit) {
      id
      inmuebleId
      titulo
      tipo
      descripcion
      fechaDocumento
      url
      fileName
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerDocumento($filter: DocumentoFilterInput!) {
    documentos(filter: $filter, limit: 1) {
      id
      inmuebleId
      titulo
      tipo
      descripcion
      fechaDocumento
      url
      fileName
      createdAt
      updatedAt
      inmueble {
        id
        nombre
      }
    }
  }
`

export const CREAR = gql`
  mutation CrearDocumento($data: DocumentoCreateInput!) {
    createDocumento(data: $data) {
      id
      titulo
      tipo
      url
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarDocumento($data: DocumentoUpdateInput!) {
    updateDocumento(data: $data) {
      id
      titulo
      tipo
      descripcion
      fechaDocumento
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarDocumento($id: ID!) {
    deleteDocumentos(filter: { id: { eq: $id } }) {
      id
    }
  }
`