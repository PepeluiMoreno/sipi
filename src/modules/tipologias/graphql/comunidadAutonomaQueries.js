import { gql } from '@apollo/client/core'

export const LISTAR_COMUNIDADES_AUTONOMAS = gql`
  query ListarComunidadesAutonomas($filters: ComunidadAutonomaFilterInputs, $pagination: PaginationInput) {
    comunidadesAutonomas(filters: $filters, pagination: $pagination) {
      items {
        id
        codigoIne
        nombre
        nombreOficial
        activo
        createdAt
        updatedAt
      }
      total
      totalPages
      page
      pageSize
    }
  }
`

export const OBTENER_COMUNIDAD_AUTONOMA = gql`
  query ObtenerComunidadAutonoma($id: ID!) {
    comunidadAutonoma(id: $id) {
      id
      codigoIne
      nombre
      nombreOficial
      activo
      createdAt
      updatedAt
    }
  }
`
