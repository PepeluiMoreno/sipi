import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Inmuebles usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarInmuebles(
    $filter: InmuebleFilterInput
    $offset: Int = 0
    $limit: Int = 50
  ) {
    inmuebles(filter: $filter, offset: $offset, limit: $limit) {
      id
      nombre
      descripcion
      direccion
      superficieConstruida
      superficieParcela
      numPlantas
      anoConstruccion
      
      # Relaciones geográficas
      municipio {
        id
        nombre
        provincia {
          id
          nombre
          comunidadAutonoma {
            id
            nombre
          }
        }
      }
      
      # Clasificación
      tipoInmueble {
        id
        nombre
      }
      
      # Estado
      estadoConservacion {
        id
        nombre
      }
      estadoTratamiento {
        id
        nombre
      }
      
      # Protección
      figuraProteccion {
        id
        nombre
      }
      
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerInmueble(
    $filter: InmuebleFilterInput!
  ) {
    inmuebles(filter: $filter, limit: 1) {
      id
      nombre
      descripcion
      direccion
      coordenadas # GeoJSON si es soportado, o string
      
      municipio {
        id
        nombre
        codigoIne
        provincia {
          id
          nombre
          comunidadAutonoma {
            id
            nombre
          }
        }
      }
      
      tipoInmueble {
        id
        nombre
      }
      
      estadoConservacion {
        id
        nombre
      }
      
      figuraProteccion {
        id
        nombre
      }
      
      diocesis {
        id
        nombre
      }
      
      # Relaciones one-to-many (usando child pagination si es necesario)
      denominaciones {
        id
        denominacion
        esPrincipal
      }
      
      inmatriculaciones {
        id
        numeroFinca
        fechaInmatriculacion
      }
      
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarInmuebles(
    $search: String!
    $limit: Int = 50
  ) {
    inmuebles(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { direccion: { ilike: $search } }
          { descripcion: { contains: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      direccion
      municipio {
        id
        nombre
      }
      tipoInmueble {
        nombre
      }
    }
  }
`

// ========================================
// MUTATIONS
// ========================================

export const CREAR = gql`
  mutation CrearInmueble($data: InmuebleCreateInput!) {
    createInmueble(data: $data) {
      id
      nombre
      direccion
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarInmueble($data: InmuebleUpdateInput!) {
    updateInmueble(data: $data) {
      id
      nombre
      direccion
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarInmueble($id: ID!) {
    deleteInmuebles(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`