import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarRolesTecnicos($filter: RolTecnicoFilter, $offset: Int = 0, $limit: Int = 50) {
    rolesTecnicos(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
    }
  }
`

export const OBTENER = gql`
  query ObtenerRolTecnico($filter: RolTecnicoFilter!) {
    rolesTecnicos(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearRolTecnico($data: RolTecnicoCreateInput!) {
    createRolTecnico(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarRolTecnico($data: RolTecnicoUpdateInput!) {
    updateRolTecnico(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarRolTecnico($id: ID!) {
    deleteRolesTecnicos(filter: { id: { eq: $id } }) {
      id
    }
  }
`