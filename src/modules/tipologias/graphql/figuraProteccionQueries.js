import { gql } from '@apollo/client/core'

export const LISTAR = gql`
  query ListarFigurasProteccion($filter: FiguraProteccionFilterInput, $offset: Int = 0, $limit: Int = 50) {
    figurasProteccion(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      # Nivel suele ser propiedad de la relación inmueble-figura, pero aquí es el catálogo base?
      # Si es el catálogo de tipos de figuras, solo nombre.
    }
  }
`
// NOTA: Esta entidad podría llamarse TipoFiguraProteccion en backend?
// Revisando schema original o nombres:
// 'figuraProteccion' (singular) en queries.js anterior.
// Asumimos 'figurasProteccion' como tabla catálogo.
// Ojo con colisión con 'InmuebleFiguraProteccion'.
// Si existe tabla 'figura_proteccion' (catálogo) vs 'inmueble_figura_proteccion' (relación).

export const OBTENER = gql`
  query ObtenerFiguraProteccion($filter: FiguraProteccionFilterInput!) {
    figurasProteccion(filter: $filter, limit: 1) {
      id
      nombre
    }
  }
`

export const CREAR = gql`
  mutation CrearFiguraProteccion($data: FiguraProteccionCreateInput!) {
    createFiguraProteccion(data: $data) {
      id
      nombre
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarFiguraProteccion($data: FiguraProteccionUpdateInput!) {
    updateFiguraProteccion(data: $data) {
      id
      nombre
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarFiguraProteccion($id: ID!) {
    deleteFigurasProteccion(filter: { id: { eq: $id } }) {
      id
    }
  }
`