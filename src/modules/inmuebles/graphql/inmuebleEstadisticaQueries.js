// modules/inmuebles/graphql/inmuebleEstadisticaQueries.js
import { gql } from '@apollo/client/core'

export const ESTADISTICAS_INMUEBLES = gql`
  query EstadisticasInmuebles($filters: InmuebleFilterInputs) {
    estadisticasInmuebles(filters: $filters) {
      totalInmuebles
      conCoordenadas
      sinCoordenadas
      esBic
      esRuina
      protegidos
      porTipoInmueble {
        tipo
        cantidad
      }
      porProvincia {
        provincia
        cantidad
      }
      porEstadoConservacion {
        estado
        cantidad
      }
    }
  }
`

export const INFORME_CONSERVACION = gql`
  query InformeConservacion($inmuebleId: ID!) {
    informeConservacion(inmuebleId: $inmuebleId) {
      inmuebleId
      estadoConservacion
      ultimasActuaciones
      recomendaciones
      prioridad
      fechaGeneracion
    }
  }
`

export const INFORME_PROTECCION = gql`
  query InformeProteccion($filters: InmuebleFilterInputs) {
    informeProteccion(filters: $filters) {
      totalProtegidos
      porNivelProteccion {
        nivel
        cantidad
      }
      inmueblesSinProteccion
      recomendaciones
      fechaGeneracion
    }
  }