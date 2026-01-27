import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarRoles($filter: RolFilterInput, $offset: Int = 0, $limit: Int = 50) {
    roles(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
      permisos
      createdAt
      updatedAt
      # usuarios_count removido por compatibilidad, usar aggregation si disponible
    }
  }
`

export const OBTENER = gql`
  query ObtenerRol($filter: RolFilterInput!) {
    roles(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
      permisos
      createdAt
      updatedAt
      usuarios {
        id
        nombre
      }
    }
  }
`

export const CREAR = gql`
  mutation CrearRol($data: RolCreateInput!) {
    createRol(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarRol($data: RolUpdateInput!) {
    updateRol(data: $data) {
      id
      nombre
      descripcion
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarRol($id: ID!) {
    deleteRoles(filter: { id: { eq: $id } }) {
      id
    }
  }
`