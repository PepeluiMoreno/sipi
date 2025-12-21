import { gql } from '@apollo/client/core'

/**
 * Queries y Mutaciones de Usuarios (Strawchemy + Auth Custom)
 */

// ==================== CRUD USUARIOS ====================

export const LISTAR = gql`
  query ListarUsuarios($filter: UsuarioFilter, $offset: Int = 0, $limit: Int = 50) {
    usuarios(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      email
      emailVerificado
      rolId
      foto
      activo
      createdAt
      updatedAt
      rol {
        id
        nombre
        permisos
      }
    }
  }
`

export const OBTENER = gql`
  query ObtenerUsuario($filter: UsuarioFilter!) {
    usuarios(filter: $filter, limit: 1) {
      id
      nombre
      email
      emailVerificado
      rolId
      foto
      activo
      createdAt
      updatedAt
      rol {
        id
        nombre
        permisos
      }
    }
  }
`

export const CREAR = gql`
  mutation CrearUsuario($data: UsuarioCreateInput!) {
    createUsuario(data: $data) {
      id
      nombre
      email
      rolId
      activo
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarUsuario($data: UsuarioUpdateInput!) {
    updateUsuario(data: $data) {
      id
      nombre
      email
      rolId
      activo
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarUsuario($id: ID!) {
    deleteUsuarios(filter: { id: { eq: $id } }) {
      id
    }
  }
`

// ==================== AUTH / CUSTOM ====================
// Estas mutaciones dependen de definiciones custom en el backend.
// Se asume que existen o se mantienen.

export const LOGIN = gql`
  mutation Login($email: String!, $password: String!) {
    login(email: $email, password: $password) {
      token
      user {
        id
        nombre
        email
        rol {
          id
          nombre
        }
      }
      success
      message
    }
  }
`

export const VERIFICAR_EMAIL = gql`
  mutation VerificarEmail($token: String!) {
    verificarEmail(token: $token) {
      success
      message
    }
  }
`

export const ASIGNAR_ROLES_USUARIO = gql`
  mutation AsignarRolesUsuario($usuarioId: ID!, $rolIds: [ID!]!) {
    # Custom mutation
    asignarRolesUsuario(usuarioId: $usuarioId, rolIds: $rolIds) {
      success
      message
      # Retorno void o status
    }
  }
`