// src/modules/inmuebles/graphql/inmuebleQueries.js
// Esquema auto-generado real: inmuebles(search, offset, limit, filters){ items{…} total }
import { gql } from '@apollo/client/core'

export const GET_INMUEBLES = gql`
  query GetInmuebles($search: String, $offset: Int = 0, $limit: Int = 200, $filters: [FilterInput!]) {
    inmuebles(search: $search, offset: $offset, limit: $limit, filters: $filters) {
      items {
        id
        nombre
        descripcion
        direccion
        referenciaCatastral
        activo
        enVenta
        estadoCicloVida
        figuraProteccionActual
        anoConstruccion
        superficieConstruida
        municipio { id nombre }
        provincia { id nombre }
        tipoInmueble { id nombre }
        estadoConservacion { id nombre }
        entidadTerritorial { id nombre tipo }
      }
      total
    }
  }
`

export const GET_INMUEBLE = gql`
  query GetInmueble($id: ID!) {
    inmueble(id: $id) {
      id
      nombre
      descripcion
      direccion
      referenciaCatastral
      fuenteCoordenadas
      comunidadAutonomaId
      provinciaId
      municipioId
      tipoInmuebleId
      estadoConservacionId
      estadoTratamientoId
      estiloArquitectonicoId
      superficieConstruida
      superficieParcela
      numPlantas
      anoConstruccion
      valorCatastral
      valorMercado
      enVenta
      activo
      estadoCicloVida
      figuraProteccionActual
      createdAt
      updatedAt
      municipio { id nombre }
      provincia { id nombre }
      comunidadAutonoma { id nombre }
      tipoInmueble { id nombre }
      estadoConservacion { id nombre }
      entidadTerritorial { id nombre tipo }
    }
  }
`

export const CREATE_INMUEBLE = gql`
  mutation CreateInmueble($data: InmuebleCreateInput!) {
    createInmueble(data: $data) { id nombre }
  }
`

export const UPDATE_INMUEBLE = gql`
  mutation UpdateInmueble($data: InmuebleUpdateInput!) {
    updateInmueble(data: $data) { id nombre }
  }
`

export const DELETE_INMUEBLE = gql`
  mutation DeleteInmueble($id: ID!) {
    deleteInmueble(id: $id)
  }
`
