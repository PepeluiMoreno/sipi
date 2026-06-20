import { gql } from '@apollo/client/core'

export const LISTAR_DOCUMENTOS_INMUEBLE = gql`
  query ListarDocumentosInmueble($inmuebleId: ID!) {
    inmuebleDocumentos(inmuebleId: $inmuebleId) {
      items {
        id
        inmuebleId
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

export const AGREGAR_DOCUMENTO_INMUEBLE = gql`
  mutation AgregarDocumentoInmueble($inmuebleId: ID!, $documentoId: ID!, $descripcion: String) {
    agregarDocumentoInmueble(inmuebleId: $inmuebleId, documentoId: $documentoId, descripcion: $descripcion) {
      success
      item {
        id
        inmuebleId
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

export const ACTUALIZAR_DOCUMENTO_INMUEBLE = gql`
  mutation ActualizarDocumentoInmueble($inmuebleId: ID!, $documentoId: ID!, $descripcion: String) {
    actualizarDocumentoInmueble(inmuebleId: $inmuebleId, documentoId: $documentoId, descripcion: $descripcion) {
      success
      item {
        id
        inmuebleId
        documentoId
        descripcion
      }
      message
    }
  }
`

export const QUITAR_DOCUMENTO_INMUEBLE = gql`
  mutation QuitarDocumentoInmueble($inmuebleId: ID!, $documentoId: ID!) {
    quitarDocumentoInmueble(inmuebleId: $inmuebleId, documentoId: $documentoId) {
      success
      message
    }
  }
`