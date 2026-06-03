import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Expedientes (ciclo de vida del inmueble), Strawchemy.
 *
 * Un Expediente es un episodio del historial del inmueble (inmatriculación,
 * secularización, enajenación, subvención, actuación, cambio de uso, ruina,
 * detección/hallazgo...). Los hallazgos llegan con estado="propuesto" y se
 * ratifican (estado="confirmado") desde la bandeja de validación.
 */

const CAMPOS = `
  id
  inmuebleId
  inmueble { id nombre }
  tipoExpedienteId
  tipo { id codigo nombre estadoResultante notificable }
  fechaInicio
  fechaFin
  estado
  titulo
  descripcion
  importe
  fuenteId
  referenciaExterna
  enlace
  confianza
  datos
  createdAt
  updatedAt
`

export const LISTAR_POR_INMUEBLE = gql`
  query ExpedientesPorInmueble($inmuebleId: String!, $offset: Int = 0, $limit: Int = 200) {
    expedientes(filter: { inmuebleId: { eq: $inmuebleId } }, offset: $offset, limit: $limit) {
      ${CAMPOS}
    }
  }
`

/** Cola de validación: hallazgos propuestos pendientes de ratificar. */
export const LISTAR_HALLAZGOS = gql`
  query Hallazgos($offset: Int = 0, $limit: Int = 100) {
    expedientes(filter: { estado: { eq: "propuesto" } }, offset: $offset, limit: $limit) {
      ${CAMPOS}
    }
  }
`

export const OBTENER = gql`
  query ObtenerExpediente($id: String!) {
    expedientes(filter: { id: { eq: $id } }, limit: 1) {
      ${CAMPOS}
      actores { id tipoActor actorId rol }
    }
  }
`

export const LISTAR_TIPOS = gql`
  query TiposExpediente {
    tiposExpediente(filter: { activo: { eq: true } }, limit: 100) {
      id codigo nombre descripcion estadoResultante notificable
    }
  }
`

export const CREAR = gql`
  mutation CrearExpediente($data: ExpedienteCreateInput!) {
    createExpediente(data: $data) { id estado tipoExpedienteId fechaInicio }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarExpediente($data: ExpedienteUpdateInput!) {
    updateExpediente(data: $data) { id estado }
  }
`

export const ELIMINAR = gql`
  mutation EliminarExpediente($id: ID!) {
    deleteExpedientes(filter: { id: { eq: $id } }) { id }
  }
`
