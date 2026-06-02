import { gql } from '@apollo/client/core'

export const LISTAR_DOCUMENTOS_ACTUACION = gql`
  query ListarDocumentosActuacion($actuacionId: ID!) {
    actuacionDocumentos(actuacionId: $actuacionId) {
      items {
        id
        actuacionId
        documentoId
        descripcion
        documento {
          id
          nombre
          tipoDocumento {
            id
            nombre
          }
          tipoLicencia {
            id
            nombre
          }
          fuenteDocumental {
            id
            nombre
          }
          mimeType
          tamaño
          fechaDocumento
        }
        createdAt
        updatedAt
      }
    }
  }
`

export const AGREGAR_DOCUMENTO_ACTUACION = gql`
  mutation AgregarDocumentoActuacion($actuacionId: ID!, $documentoId: ID!, $descripcion: String) {
    agregarDocumentoActuacion(actuacionId: $actuacionId, documentoId: $documentoId, descripcion: $descripcion) {
      success
      item {
        id
        actuacionId
        documentoId
        descripcion
        documento {
          id
          nombre
          tipoDocumento {
            id
            nombre
          }
        }
      }
      message
    }
  }
`

export const ACTUALIZAR_DOCUMENTO_ACTUACION = gql`
  mutation ActualizarDocumentoActuacion($actuacionId: ID!, $documentoId: ID!, $descripcion: String) {
    actualizarDocumentoActuacion(actuacionId: $actuacionId, documentoId: $documentoId, descripcion: $descripcion) {
      success
      item {
        id
        actuacionId
        documentoId
        descripcion
      }
      message
    }
  }
`

export const QUITAR_DOCUMENTO_ACTUACION = gql`
  mutation QuitarDocumentoActuacion($actuacionId: ID!, $documentoId: ID!) {
    quitarDocumentoActuacion(actuacionId: $actuacionId, documentoId: $documentoId) {
      success
      message
    }
  }
`