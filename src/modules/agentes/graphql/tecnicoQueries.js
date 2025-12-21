import { gql } from '@apollo/client/core'

/**
 * Queries y Mutations para Técnicos usando Strawchemy
 */

// ========================================
// QUERIES
// ========================================

export const LISTAR = gql`
  query ListarTecnicos(
    $filter: TecnicoFilter
    $offset: Int = 0
    $limit: Int = 50
  ) {
    tecnicos(filter: $filter, offset: $offset, limit: $limit) {
      id
      tipoIdentificacion
      numeroIdentificacion
      nombre
      razonSocial
      email
      telefono
      direccion
      codigoPostal
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
      rolTecnico {
        id
        nombre
      }
      colegioProfesional {
        id
        nombre
      }
      numeroColegiado
      fechaColegiacion
      createdAt
      updatedAt
    }
  }
`

export const OBTENER = gql`
  query ObtenerTecnico(
    $filter: TecnicoFilter!
  ) {
    tecnicos(filter: $filter, limit: 1) {
      id
      tipoIdentificacion
      numeroIdentificacion
      nombre
      razonSocial
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
        codigoIne
        provincia {
          id
          nombre
        }
      }
      rolTecnico {
        id
        nombre
      }
      colegioProfesional {
        id
        nombre
      }
      numeroColegiado
      fechaColegiacion
      createdAt
      updatedAt
    }
  }
`

export const BUSCAR = gql`
  query BuscarTecnicos(
    $search: String!
    $limit: Int = 50
  ) {
    tecnicos(
      filter: {
        _or: [
          { nombre: { ilike: $search } }
          { razonSocial: { ilike: $search } }
          { numeroIdentificacion: { contains: $search } }
          { email: { ilike: $search } }
        ]
      }
      limit: $limit
    ) {
      id
      nombre
      razonSocial
      numeroIdentificacion
      email
      telefono
      municipio {
        id
        nombre
      }
      rolTecnico {
        id
        nombre
      }
    }
  }
`

export const LISTAR_POR_MUNICIPIO = gql`
  query ListarTecnicosPorMunicipio(
    $municipioId: ID!
    $offset: Int = 0
    $limit: Int = 50
  ) {
    tecnicos(
      filter: { municipioId: { eq: $municipioId } }
      offset: $offset
      limit: $limit
    ) {
      id
      nombre
      razonSocial
      direccion
      telefono
      municipio {
        id
        nombre
      }
      rolTecnico {
        id
        nombre
      }
    }
  }
`

// ========================================
// MUTATIONS
// ========================================

export const CREAR = gql`
  mutation CrearTecnico($data: TecnicoCreateInput!) {
    createTecnico(data: $data) {
      id
      nombre
      razonSocial
      numeroIdentificacion
      email
      telefono
      municipio {
        id
        nombre
      }
      rolTecnico {
        id
        nombre
      }
      createdAt
    }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarTecnico($data: TecnicoUpdateInput!) {
    updateTecnico(data: $data) {
      id
      nombre
      razonSocial
      numeroIdentificacion
      email
      telefono
      direccion
      codigoPostal
      municipio {
        id
        nombre
      }
      rolTecnico {
        id
        nombre
      }
      colegioProfesional {
        id
        nombre
      }
      updatedAt
    }
  }
`

export const ELIMINAR = gql`
  mutation EliminarTecnico($id: ID!) {
    deleteTecnicos(filter: { id: { eq: $id } }) {
      id
      nombre
    }
  }
`
