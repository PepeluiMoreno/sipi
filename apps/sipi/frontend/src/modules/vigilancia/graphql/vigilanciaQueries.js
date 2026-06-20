import { gql } from '@apollo/client/core'

// Formato genérico compatible con useAgenteBase (entityName = 'procesosVigilancia').
// `parametros` es un JSON scalar (objeto).

export const LISTAR = gql`
  query ListarProcesos($search: String, $offset: Int = 0, $limit: Int = 50, $filters: [FilterInput!]) {
    procesosVigilancia(search: $search, offset: $offset, limit: $limit, filters: $filters) {
      items {
        id nombre tipo descripcion activo frecuenciaCron severidadDefecto parametros
      }
      total
    }
  }
`

export const CREAR = gql`
  mutation CrearProceso($data: ProcesoVigilanciaCreateInput!) {
    createProcesoVigilancia(data: $data) { id }
  }
`

export const ACTUALIZAR = gql`
  mutation ActualizarProceso($data: ProcesoVigilanciaUpdateInput!) {
    updateProcesoVigilancia(data: $data) { id }
  }
`

export const ELIMINAR = gql`
  mutation EliminarProceso($id: ID!) {
    deleteProcesoVigilancia(id: $id)
  }
`

export const PURGAR = gql`
  mutation PurgarProceso($id: ID!) {
    purgarProcesoVigilancia(id: $id)
  }
`

// Últimos hallazgos de un proceso (pestaña "Hallazgos" del detalle).
export const HALLAZGOS_PROCESO = gql`
  query HallazgosProceso($filters: [FilterInput!], $limit: Int = 25) {
    hallazgos(filters: $filters, limit: $limit, sort: [{ field: "fecha_deteccion", direction: DESC }]) {
      items {
        id fuente tipoEvento estado certeza confianza titulo descripcion
        urlEvidencia fechaEvento fechaDeteccion
      }
      total
    }
  }
`

// Probar (dry-run, no guarda) un proceso ahora mismo.
export const PROBAR_PROCESO = gql`
  mutation ProbarProceso($procesoId: ID!, $fuenteId: String) {
    probarProcesoVigilancia(procesoId: $procesoId, fuenteId: $fuenteId) {
      ok mensaje creados muestras { fuente titulo url precio score }
    }
  }
`

// Ejecutar (fetch real + crea Hallazgo) un proceso ahora mismo.
export const EJECUTAR_PROCESO = gql`
  mutation EjecutarProceso($procesoId: ID!, $fuenteId: String) {
    ejecutarProcesoVigilancia(procesoId: $procesoId, fuenteId: $fuenteId) {
      ok mensaje creados muestras { fuente titulo url precio score }
    }
  }
`
