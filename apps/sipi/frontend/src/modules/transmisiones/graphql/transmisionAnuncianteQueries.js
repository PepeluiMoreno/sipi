import { gql } from '@apollo/client/core'

export const LISTAR_ANUNCIANTES = gql`
  query ListarAnunciantes($transmisionId: ID!) {
    transmisionAnunciantes(transmisionId: $transmisionId) {
      items {
        id
        transmisionId
        agenciaInmobiliariaId
        agenciaInmobiliaria {
          id
          nombre
          localidad {
            id
            nombre
          }
        }
        createdAt
        updatedAt
      }
    }
  }
`

export const AGREGAR_ANUNCIANTE = gql`
  mutation AgregarAnunciante($transmisionId: ID!, $agenciaInmobiliariaId: ID!) {
    agregarAnunciante(transmisionId: $transmisionId, agenciaInmobiliariaId: $agenciaInmobiliariaId) {
      success
      item {
        id
        agenciaInmobiliariaId
        agenciaInmobiliaria {
          id
          nombre
        }
      }
      message
    }
  }
`

export const QUITAR_ANUNCIANTE = gql`
  mutation QuitarAnunciante($transmisionId: ID!, $agenciaInmobiliariaId: ID!) {
    quitarAnunciante(transmisionId: $transmisionId, agenciaInmobiliariaId: $agenciaInmobiliariaId) {
      success
      message
    }
  }
`