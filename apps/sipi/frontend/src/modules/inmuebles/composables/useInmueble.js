// src/modules/inmuebles/composables/useInmueble.js
// Datos reales vía GraphQL auto-generado. SIN mock.
import { ref, computed } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import {
  GET_INMUEBLES,
  GET_INMUEBLE,
  CREATE_INMUEBLE,
  UPDATE_INMUEBLE,
  DELETE_INMUEBLE
} from '../graphql/inmuebleQueries'

export function useInmueble() {
  const inmuebles = ref([])
  const inmueble = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const { resolveClient } = useApolloClient()
  const getClient = () => resolveClient()

  const hasInmuebles = computed(() => inmuebles.value.length > 0)
  const isEmpty = computed(() => !loading.value && !inmuebles.value.length)
  const filteredCount = computed(() => inmuebles.value.length)

  // Traduce el objeto de filtros (claves camelCase = columnas) a FilterInput[]:
  // array → IN, escalar → EQ. Ignora `search` (va aparte) y objetos (p.ej. estados:{}).
  const construirFilters = (p = {}) => {
    const filters = []
    for (const [campo, valor] of Object.entries(p)) {
      if (campo === 'search') continue
      if (valor === null || valor === undefined || valor === '') continue
      if (Array.isArray(valor)) {
        if (valor.length) filters.push({ field: campo, operator: 'IN', values: valor.map(String) })
        continue
      }
      if (typeof valor === 'object') continue
      filters.push({ field: campo, operator: 'EQ', value: String(valor) })
    }
    return filters
  }

  const listar = async (filterParams = {}) => {
    loading.value = true
    error.value = null
    try {
      const variables = { offset: 0, limit: 200 }
      if (typeof filterParams?.search === 'string' && filterParams.search.trim()) {
        variables.search = filterParams.search.trim()
      }
      const filters = construirFilters(filterParams)
      if (filters.length) variables.filters = filters

      const { data } = await getClient().query({
        query: GET_INMUEBLES,
        variables,
        fetchPolicy: 'network-only'
      })
      inmuebles.value = data?.inmuebles?.items || []
      return { items: inmuebles.value, total: data?.inmuebles?.total ?? inmuebles.value.length }
    } catch (err) {
      error.value = err.message
      console.error('Error al listar inmuebles:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const obtener = async (id) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await getClient().query({
        query: GET_INMUEBLE,
        variables: { id },
        fetchPolicy: 'network-only'
      })
      inmueble.value = data?.inmueble || null
      return inmueble.value
    } catch (err) {
      error.value = err.message
      console.error('Error al obtener inmueble:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const crear = async (input) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await getClient().mutate({
        mutation: CREATE_INMUEBLE,
        variables: { data: input }
      })
      inmueble.value = data?.createInmueble
      return inmueble.value
    } catch (err) {
      error.value = err.message
      console.error('Error al crear inmueble:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const actualizar = async (id, input) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await getClient().mutate({
        mutation: UPDATE_INMUEBLE,
        variables: { data: { id, ...input } }
      })
      inmueble.value = data?.updateInmueble
      return inmueble.value
    } catch (err) {
      error.value = err.message
      console.error('Error al actualizar inmueble:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const eliminar = async (id) => {
    loading.value = true
    error.value = null
    try {
      await getClient().mutate({ mutation: DELETE_INMUEBLE, variables: { id } })
      inmuebles.value = inmuebles.value.filter((i) => i.id !== id)
      return true
    } catch (err) {
      error.value = err.message
      console.error('Error al eliminar inmueble:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // Catálogos: pendientes de cablear a las tipologías reales ({items}). Sin mock.
  const obtenerCatalogos = async () => ({
    estados: [],
    tiposInmueble: [],
    comunidadesAutonomas: [],
    provincias: [],
    localidades: [],
    registrosPropiedad: [],
    tiposDocumento: [],
    estadosConservacion: []
  })

  return {
    inmuebles,
    inmueble,
    loading,
    error,
    hasInmuebles,
    isEmpty,
    filteredCount,
    listar,
    obtener,
    crear,
    actualizar,
    eliminar,
    obtenerCatalogos
  }
}
