import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Documentos usando Strawchemy
 */

export const LISTAR = gql`
  query ListarDocumentos($filter: DocumentoFilter, $offset: Int = 0, $limit: Int = 50) {
    documentos(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
      tipoDocumentoId
      tipoDocumento {
        id
        nombre
      }
      tipoLicenciaId
      fuenteDocumentalId
      mimeType
      tamaño
      fechaDocumento
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerDocumento($filter: DocumentoFilter!) {
    documentos(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
      tipoDocumentoId
      tipoDocumento {
        id
        nombre
      }
      tipoLicenciaId
      fuenteDocumentalId
      mimeType
      tamaño
      fechaDocumento
      createdAt
      updatedAt
      
      # Relaciones inversas (si soportadas por schema, si no, se eliminan)
      inmuebles {
        id
        inmueble {
          id
          nombre
        }
      }
      actuaciones {
        id
        actuacion {
          id
          tipo
        }
      }
    }
  }
`

export const CREAR = gql`
  mutation CrearDocumento($data: DocumentoCreateInput!) {
    createDocumento(data: $data) {
      id
      nombre
      tipoDocumentoId
      mimeType
      tamaño
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarDocumento($data: DocumentoUpdateInput!) {
    updateDocumento(data: $data) {
      id
      nombre
      tipoDocumentoId
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