import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarMunicipios($filter: MunicipioFilterInput, $limit: Int = 50, $offset: Int = 0) {
    municipios(filter: $filter, limit: $limit, offset: $offset) {
      id
      nombre
    }
  }
`
