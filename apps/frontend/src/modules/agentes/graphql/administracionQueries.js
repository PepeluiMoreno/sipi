import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Administraciones usando Strawchemy
 * 
 * Diferencias con el schema anterior:
 * - Paginación: offset/limit en vez de page/pageSize
 * - Filtros: estructura filter con operadores (eq, contains, ilike, etc.)
 * - Respuestas: array directo, sin wrapping de {items, total, page}
 * - Mutations: parámetro `data` en vez de `input`
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarAdministraciones(
    $filter: AdministracionFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    administraciones(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER_ADMINISTRACION = gql`
  query ObtenerAdministracion(
    $filter: AdministracionFilterInput!
  ) {
    administraciones(filter: $filter, limit: 1) {
      id
      nombre
      ambito
      nombreResponsable
      numeroIdentificacion
      email
      telefono
      direccion
      codigoPostal
      municipioSede {
        id
        nombre
      }
    }
  }
`

export const BUSCAR_ADMINISTRACIONES = gql`
  query BuscarAdministraciones(
    $search: String!
    $limit: Int = 50
  ) {
    administraciones(
      filter: {
        nombre: { ilike: $search }
      }
      limit: $limit
    ) {
      id
      nombre
      ambito
      email
    }
  }
`

export const LISTAR_POR_AMBITO = gql`
  query ListarAdministracionesPorAmbito(
    $ambito: String!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    administraciones(
      filter: { ambito: { eq: $ambito } }
      offset: $offset
      limit: $limit
    ) {
      id
      nombre
      ambito
      email
    }
  }
`

export const LISTAR_POR_MUNICIPIO = gql`
  query ListarAdministracionesPorMunicipio(
    $municipioId: ID!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    administraciones(
      filter: { municipioId: { eq: $municipioId } }
      offset: $offset
      limit: $limit
    ) {
      id
      nombre
      ambito
      email
    }
  }
`

// ========================================
// MUTATIONS
// ========================================

export const CREAR_ADMINISTRACION = gql`
  mutation CrearAdministracion($data: AdministracionCreateInput!) {
    createAdministracion(data: $data) {
      id
      nombre
      ambito
      nombreResponsable
      email
      telefono
      municipioSede {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR_ADMINISTRACION = gql`
  mutation ActualizarAdministracion($data: AdministracionUpdateInput!) {
    updateAdministracion(data: $data) {
      id
      nombre
      ambito
      nombreResponsable
      email
      telefono
      direccion
      codigoPostal
      municipioSede {
        id
        nombre
      }
      updatedAt
    }
  }
`

export const ACTUALIZAR_ADMINISTRACIONES_LOTE = gql`
  mutation ActualizarAdministracionesLote($data: [AdministracionUpdateInput!]!) {
    updateAdministraciones(data: $data) {
      id
      nombre
      updatedAt
    }
  }
`

export const ELIMINAR_ADMINISTRACION = gql`
  mutation EliminarAdministracion($id: ID!) {
    deleteAdministraciones(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`

export const ELIMINAR_ADMINISTRACIONES_FILTRO = gql`
  mutation EliminarAdministracionesFiltro($filter: AdministracionFilterInput!) {
    deleteAdministraciones(filter: $filter) {
      id
      nombre
    }
  }
`

// ========================================
// QUERIES DE TITULARES
// ========================================

export const CREAR_TITULAR = gql`
  mutation CrearAdministracionTitular($data: AdministracionTitularCreateInput!) {
    createAdministracionTitular(data: $data) {
      id
      nombre
      apellidos
      numeroIdentificacion
      fechaInicio
      fechaFin
      cargo
      administracion {
        id
        nombre
      }
    }
  }
`

export const ACTUALIZAR_TITULAR = gql`
  mutation ActualizarAdministracionTitular($data: AdministracionTitularUpdateInput!) {
    updateAdministracionTitular(data: $data) {
      id
      nombre
      apellidos
      fechaInicio
      fechaFin
      cargo
    }
  }
`
