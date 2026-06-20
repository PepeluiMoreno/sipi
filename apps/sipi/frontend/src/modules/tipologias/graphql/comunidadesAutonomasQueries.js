import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarComunidadesAutonomas($filter: ComunidadAutonomaFilterInput, $limit: Int = 50, $offset: Int = 0) {
    comunidadesAutonomas(filter: $filter, limit: $limit, offset: $offset) {
      id
      nombre
    }
  }
`
