import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Figuras de Protección usando Strawchemy
 * Entidad base: FiguraProteccion -> figuraProtecciones
 */

export const LISTAR = gql`
  query ListarFigurasProteccion($filter: FiguraProteccionFilter, $offset: Int = 0, $limit: Int = 50) {
    figuraProtecciones(filter: $filter, offset: $offset, limit: $limit) {
      id
      inmuebleId
      tipo
      nivel
      fechaDeclaracion
      observaciones
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerFiguraProteccion($filter: FiguraProteccionFilter!) {
    figuraProtecciones(filter: $filter, limit: 1) {
      id
      inmuebleId
      tipo
      nivel
      fechaDeclaracion
      observaciones
      createdAt
      updatedAt
    }
  }
`

export const CREAR = gql`
  mutation CrearFiguraProteccion($data: FiguraProteccionCreateInput!) {
    createFiguraProteccion(data: $data) {
      id
      tipo
      nivel
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarFiguraProteccion($data: FiguraProteccionUpdateInput!) {
    updateFiguraProteccion(data: $data) {
      id
      tipo
      nivel
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarFiguraProteccion($id: ID!) {
    deleteFiguraProtecciones(filter: { id: { eq: $id } }) {
      id
    }
  }
`
