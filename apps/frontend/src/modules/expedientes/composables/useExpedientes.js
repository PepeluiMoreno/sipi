import { ref } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import {
  LISTAR_POR_INMUEBLE, LISTAR_HALLAZGOS, OBTENER, LISTAR_TIPOS,
  CREAR, ACTUALIZAR, ELIMINAR
} from '../graphql/expedienteQueries'

/**
 * Composable de expedientes. Usa el cliente Apollo directamente para poder
 * invocar query/mutate dentro de funciones async.
 */
export function useExpedientes() {
  const { resolveClient } = useApolloClient()
  const loading = ref(false)
  const error = ref(null)

  async function _run(fn) {
    loading.value = true
    error.value = null
    try {
      return await fn(resolveClient())
    } catch (err) {
      error.value = err?.message || String(err)
      console.error('[useExpedientes]', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const listarPorInmueble = (inmuebleId) =>
    _run(async (c) => {
      const { data } = await c.query({
        query: LISTAR_POR_INMUEBLE, variables: { inmuebleId },
        fetchPolicy: 'network-only'
      })
      return (data?.expedientes || []).slice().sort(_porFechaDesc)
    })

  const listarHallazgos = () =>
    _run(async (c) => {
      const { data } = await c.query({ query: LISTAR_HALLAZGOS, fetchPolicy: 'network-only' })
      return (data?.expedientes || []).slice().sort(_porConfianza)
    })

  const obtener = (id) =>
    _run(async (c) => {
      const { data } = await c.query({ query: OBTENER, variables: { id }, fetchPolicy: 'network-only' })
      return data?.expedientes?.[0] || null
    })

  const listarTipos = () =>
    _run(async (c) => {
      const { data } = await c.query({ query: LISTAR_TIPOS, fetchPolicy: 'cache-first' })
      return data?.tiposExpediente || []
    })

  const crear = (data) =>
    _run(async (c) => {
      const res = await c.mutate({ mutation: CREAR, variables: { data } })
      return res.data?.createExpediente
    })

  const actualizar = (data) =>
    _run(async (c) => {
      const res = await c.mutate({ mutation: ACTUALIZAR, variables: { data } })
      return res.data?.updateExpediente
    })

  const eliminar = (id) =>
    _run(async (c) => {
      const res = await c.mutate({ mutation: ELIMINAR, variables: { id } })
      return res.data?.deleteExpedientes
    })

  /** Ratifica un hallazgo: propuesto -> confirmado.
   *  NOTA backend: al confirmar, el servicio debe recalcular
   *  Inmueble.estado_actual a partir del estado_resultante del tipo. */
  const ratificar = (id) => actualizar({ id, estado: 'confirmado' })
  const descartar = (id) => actualizar({ id, estado: 'descartado' })

  return {
    loading, error,
    listarPorInmueble, listarHallazgos, obtener, listarTipos,
    crear, actualizar, eliminar, ratificar, descartar
  }
}

function _porFechaDesc(a, b) {
  const fa = a.fechaInicio || a.createdAt || ''
  const fb = b.fechaInicio || b.createdAt || ''
  return fb.localeCompare(fa)
}
function _porConfianza(a, b) {
  const orden = { ALTA: 0, MEDIA: 1, BAJA: 2 }
  return (orden[a.confianza] ?? 3) - (orden[b.confianza] ?? 3)
}
