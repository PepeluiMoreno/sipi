import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarProvincias($filter: ProvinciaFilterInput, $limit: Int = 50, $offset: Int = 0) {
    provincias(filter: $filter, limit: $limit, offset: $offset) {
      id
      nombre
    }
  }
`
