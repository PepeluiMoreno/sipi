import { gql } from '@apollo/client/core'

// API genérica: entidadesReligiosas(search, offset, limit, filters) { items { … } total }
export const LISTAR = gql`
  query ListarEntidadesReligiosas($search: String, $offset: Int = 0, $limit: Int = 50, $filters: [FilterInput!]) {
    entidadesReligiosas(search: $search, offset: $offset, limit: $limit, filters: $filters) {
      items {
        id nombre nombreCompleto confesion nif activa esTerritorial
        referenciaCatastral diocesisId parroquiaId municipioId tipoEntidadId
        tipoEntidad { id nombre }
        municipioSede { id nombre }
        diocesis { nombre }
      }
      total
    }
  }
`

// Catálogo de tipos de entidad religiosa (9 filas). Esquema real: { items { id nombre } total }
export const LISTAR_TIPOS = gql`
  query ListarTiposEntidadReligiosa {
    tiposEntidadReligiosa(limit: 100) {
      items { id nombre }
    }
  }
`

export const CREAR = gql`
  mutation CrearEntidadReligiosa($data: EntidadReligiosaCreateInput!) {
    createEntidadReligiosa(data: $data) { id nombre }
  }
`
export const ACTUALIZAR = gql`
  mutation ActualizarEntidadReligiosa($data: EntidadReligiosaUpdateInput!) {
    updateEntidadReligiosa(data: $data) { id nombre }
  }
`
export const ELIMINAR = gql`
  mutation EliminarEntidadReligiosa($id: ID!) { deleteEntidadReligiosa(id: $id) }
`
export const PURGAR = gql`
  mutation PurgarEntidadReligiosa($id: ID!) { purgarEntidadReligiosa(id: $id) }
`
