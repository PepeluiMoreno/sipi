import { gql } from '@apollo/client/core'

// Listar catálogo simple (nombre, descripción)
export const LISTAR_CATALOGO_SIMPLE = gql`
  query ListarCatalogoSimple($catalogo: String!, $filters: CatalogoSimpleFilters, $pagination: PaginationInput) {
    catalogoSimple(catalogo: $catalogo, filters: $filters, pagination: $pagination) {
      items {
        id
        nombre
        descripcion
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

// Obtener item simple
export const OBTENER_CATALOGO_SIMPLE = gql`
  query ObtenerCatalogoSimple($catalogo: String!, $id: ID!) {
    catalogoSimpleItem(catalogo: $catalogo, id: $id) {
      id
      nombre
      descripcion
      createdAt
      updatedAt
    }
  }
`

// Crear item simple
export const CREAR_CATALOGO_SIMPLE = gql`
  mutation CrearCatalogoSimple($catalogo: String!, $input: CatalogoSimpleInput!) {
    crearCatalogoSimple(catalogo: $catalogo, input: $input) {
      success
      item {
        id
        nombre
        descripcion
        createdAt
        updatedAt
      }
      message
    }
  }
`

// Actualizar item simple
export const ACTUALIZAR_CATALOGO_SIMPLE = gql`
  mutation ActualizarCatalogoSimple($catalogo: String!, $id: ID!, $input: CatalogoSimpleInput!) {
    actualizarCatalogoSimple(catalogo: $catalogo, id: $id, input: $input) {
      success
      item {
        id
        nombre
        descripcion
        updatedAt
      }
      message
    }
  }
`

// Eliminar item simple
export const ELIMINAR_CATALOGO_SIMPLE = gql`
  mutation EliminarCatalogoSimple($catalogo: String!, $id: ID!) {
    eliminarCatalogoSimple(catalogo: $catalogo, id: $id) {
      success
      message
    }
  }
`