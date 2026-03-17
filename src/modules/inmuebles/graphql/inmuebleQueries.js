// src/modules/inmuebles/graphql/inmuebleQueries.js
import { gql } from '@apollo/client/core'

export const GET_INMUEBLES = gql`
  query GetInmuebles($filters: InmuebleFilters) {
    inmuebles(filters: $filters) {
      items {
        id
        denominacion_principal
        direccion
        codigo_postal
        provincia
        localidad
        latitud
        longitud
        tipo_inmueble
        estado
        codigo_bien_interes_cultural
        superficie_construida
        superficie_parcela
        fecha_construccion
        imagen
      }
      total
    }
  }
`

export const GET_INMUEBLE = gql`
  query GetInmueble($id: ID!) {
    inmueble(id: $id) {
      id
      denominacion_principal
      direccion
      codigo_postal
      provincia
      localidad
      latitud
      longitud
      tipo_inmueble
      estado
      codigo_bien_interes_cultural
      superficie_construida
      superficie_parcela
      fecha_construccion
      fecha_inmatriculacion
      registro_propiedad
      numero_finca
      descripcion
      imagen
      created_at
      updated_at
    }
  }
`

export const CREATE_INMUEBLE = gql`
  mutation CreateInmueble($input: InmuebleInput!) {
    createInmueble(input: $input) {
      id
      denominacion_principal
    }
  }
`

export const UPDATE_INMUEBLE = gql`
  mutation UpdateInmueble($id: ID!, $input: InmuebleInput!) {
    updateInmueble(id: $id, input: $input) {
      id
      denominacion_principal
    }
  }
`

export const DELETE_INMUEBLE = gql`
  mutation DeleteInmueble($id: ID!) {
    deleteInmueble(id: $id) {
      success
    }
  }
`