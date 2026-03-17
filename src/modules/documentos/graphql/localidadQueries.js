// src/modules/tipologias/graphql/localidadesQueries.js

export const LOCALIDAD_QUERIES = {
  LISTAR: `
    query ListarLocalidades($filtros: FiltrosLocalidadInput) {
      localidades(filtros: $filtros) {
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
    }
  `,
  OBTENER: `
    query ObtenerLocalidad($id: ID!) {
      localidad(id: $id) {
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
    }
  `,
  CREAR: `
    mutation CrearLocalidad($input: LocalidadInput!) {
      crearLocalidad(input: $input) {
        id
        nombre
      }
    }
  `,
  ACTUALIZAR: `
    mutation ActualizarLocalidad($id: ID!, $input: LocalidadInput!) {
      actualizarLocalidad(id: $id, input: $input) {
        id
        nombre
      }
    }
  `,
  ELIMINAR: `
    mutation EliminarLocalidad($id: ID!) {
      eliminarLocalidad(id: $id)
    }
  `
}