import { gql } from '@apollo/client/core'

// ProcesoVigilancia se auto-expone por el mapper del backend.
// `parametros` es un JSON scalar (objeto), no un string.

export const PROCESOS_VIGILANCIA = gql`
  query ProcesosVigilancia {
    procesosVigilancia(limit: 200, offset: 0) {
      items {
        id
        nombre
        tipo
        descripcion
        activo
        frecuenciaCron
        severidadDefecto
        parametros
      }
    }
  }
`

export const CREAR_PROCESO = gql`
  mutation CrearProceso($data: ProcesoVigilanciaCreateInput!) {
    createProcesoVigilancia(data: $data) {
      id
    }
  }
`

export const ACTUALIZAR_PROCESO = gql`
  mutation ActualizarProceso($data: ProcesoVigilanciaUpdateInput!) {
    updateProcesoVigilancia(data: $data) {
      id
    }
  }
`
