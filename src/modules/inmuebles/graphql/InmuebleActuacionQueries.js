import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Actuaciones usando Strawchemy
 * Entidad base: Actuacion -> actuaciones
 */

export const LISTAR = gql`
  query ListarActuaciones($filter: ActuacionFilter, $offset: Int = 0, $limit: Int = 50) {
    actuaciones(filter: $filter, offset: $offset, limit: $limit) {
      id
      inmuebleId
      tipo
      descripcion
      fechaInicio
      fechaFin
      estado
      presupuesto
      responsable
      observaciones
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerActuacion($filter: ActuacionFilter!) {
    actuaciones(filter: $filter, limit: 1) {
      id
      inmuebleId
      tipo
      descripcion
      fechaInicio
      fechaFin
      estado
      presupuesto
      responsable
      observaciones
      createdAt
      updatedAt
    }
  }
`

export const CREAR = gql`
  mutation CrearActuacion($data: ActuacionCreateInput!) {
    createActuacion(data: $data) {
      id
      tipo
      fechaInicio
      estado
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarActuacion($data: ActuacionUpdateInput!) {
    updateActuacion(data: $data) {
      id
      tipo
      fechaInicio
      estado
      descripcion
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarActuacion($id: ID!) {
    deleteActuaciones(filter: { id: { eq: $id } }) {
      id
    }
  }
`