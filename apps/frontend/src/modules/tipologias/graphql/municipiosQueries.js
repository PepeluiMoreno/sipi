import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarMunicipios($filter: MunicipioFilterInput, $limit: Int = 500, $offset: Int = 0) {
    municipios(filter: $filter, limit: $limit, offset: $offset) {
      id
      nombre
      provincia {
        id
        nombre
      }
    }
  }
`

export const OBTENER = gql`
  query ObtenerMunicipio($filter: MunicipioFilterInput!) {
    municipios(filter: $filter, limit: 1) {
      id
      nombre
      provincia {
        id
        nombre
      }
    }
  }
`

export const BUSCAR = gql`
  query BuscarMunicipios($search: String!, $limit: Int = 50) {
    municipios(
      filter: { nombre: { ilike: $search } }
      limit: $limit
    ) {
      id
      nombre
      provincia {
        id
        nombre
      }
    }
  }
`

export const LISTAR_POR_PROVINCIA = gql`
  query ListarMunicipiosPorProvincia($provinciaId: ID!, $limit: Int = 500) {
    municipios(
      filter: { provinciaId: { eq: $provinciaId } }
      limit: $limit
    ) {
      id
      nombre
    }
  }
`
