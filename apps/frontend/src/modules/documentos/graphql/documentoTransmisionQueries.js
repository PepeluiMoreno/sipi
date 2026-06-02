import { gql } from '@apollo/client/core'

export const LISTAR_DOCUMENTOS_TRANSMISION = gql`
  query ListarDocumentosTransmision($transmisionId: ID!) {
    transmisionDocumentos(transmisionId: $transmisionId) {
      items {
        id
        transmisionId
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

export const AGREGAR_DOCUMENTO_TRANSMISION = gql`
  mutation AgregarDocumentoTransmision($transmisionId: ID!, $documentoId: ID!, $descripcion: String) {
    agregarDocumentoTransmision(transmisionId: $transmisionId, documentoId: $documentoId, descripcion: $descripcion) {
      success
      item {
        id
        transmisionId
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

export const ACTUALIZAR_DOCUMENTO_TRANSMISION = gql`
  mutation ActualizarDocumentoTransmision($transmisionId: ID!, $documentoId: ID!, $descripcion: String) {
    actualizarDocumentoTransmision(transmisionId: $transmisionId, documentoId: $documentoId, descripcion: $descripcion) {
      success
      item {
        id
        transmisionId
        documentoId
        descripcion
      }
      message
    }
  }
`

export const QUITAR_DOCUMENTO_TRANSMISION = gql`
  mutation QuitarDocumentoTransmision($transmisionId: ID!, $documentoId: ID!) {
    quitarDocumentoTransmision(transmisionId: $transmisionId, documentoId: $documentoId) {
      success
      message
    }
  }
`