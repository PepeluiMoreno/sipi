import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarProvincias($filter: ProvinciaFilterInput, $limit: Int = 100, $offset: Int = 0) {
    provincias(filter: $filter, limit: $limit, offset: $offset) {
      id
      nombre
      comunidadAutonoma {
        id
        nombre
      }
    }
  }
`

export const OBTENER = gql`
  query ObtenerProvincia($filter: ProvinciaFilterInput!) {
    provincias(filter: $filter, limit: 1) {
      id
      nombre
      comunidadAutonoma {
        id
        nombre
      }
    }
  }
`
