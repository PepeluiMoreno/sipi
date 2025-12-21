import { ref, computed } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import * as queries from '../graphql/administracionQueries.js'

/**
 * Composable para Administraciones adaptado a Strawchemy
 * 
 * Cambios principales:
 * - Paginación con offset/limit en vez de page/pageSize
 * - Filtros avanzados usando operadores de Strawchemy
 * - Sin wrapping de respuestas (acceso directo al array)
 * - Soporte para agregaciones automáticas
 */
export function useAdministracion() {
  const items = ref([])
  const item = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Paginación offset-based
  const offset = ref(0)
  const limit = ref(50)
  const hasMore = ref(true)

  // Filtros activos
  const activeFilters = ref({})

  // Computed
  const hasItems = computed(() => items.value.length > 0)
  const isEmpty = computed(() => !loading.value && items.value.length === 0)
  const totalCargados = computed(() => items.value.length)

  /**
   * Listar administraciones con filtros
   * @param {Object} filters - Filtros de Strawchemy
   * @param {Boolean} append - Si es true, añade a los items existentes (para paginación infinita)
   */
  const listar = async (filters = {}, append = false) => {
    loading.value = true
    error.value = null

    try {
      const { onResult, onError } = useQuery(
        queries.LISTAR_ADMINISTRACIONES,
        {
          filter: filters,
          offset: append ? offset.value : 0,
          limit: limit.value
        },
        {
          fetchPolicy: 'network-only' // Siempre consultar al servidor
        }
      )

      return new Promise((resolve, reject) => {
        onResult(({ data }) => {
          const resultados = data?.administraciones || []

          if (append) {
            items.value = [...items.value, ...resultados]
          } else {
            items.value = resultados
            offset.value = 0
          }

          // Si recibimos menos items que el limit, no hay más
          hasMore.value = resultados.length === limit.value

          // Guardar filtros activos
          activeFilters.value = filters

          loading.value = false
          resolve(items.value)
        })

        onError((err) => {
          error.value = `Error al cargar administraciones: ${err.message}`
          console.error('Error en listar administraciones:', err)
          loading.value = false
          reject(err)
        })
      })
    } catch (err) {
      error.value = `Error al cargar administraciones: ${err.message}`
      loading.value = false
      throw err
    }
  }

  /**
   * Obtener una administración por ID
   * @param {String} id - UUID de la administración
   */
  const obtener = async (id) => {
    loading.value = true
    error.value = null

    try {
      const { onResult, onError } = useQuery(
        queries.OBTENER_ADMINISTRACION,
        {
          filter: { id: { eq: id } }
        },
        {
          fetchPolicy: 'network-only'
        }
      )

      return new Promise((resolve, reject) => {
        onResult(({ data }) => {
          const resultados = data?.administraciones || []
          item.value = resultados.length > 0 ? resultados[0] : null
          loading.value = false
          resolve(item.value)
        })

        onError((err) => {
          error.value = `Error al obtener administración: ${err.message}`
          loading.value = false
          reject(err)
        })
      })
    } catch (err) {
      error.value = `Error al obtener administración: ${err.message}`
      loading.value = false
      throw err
    }
  }

  /**
   * Buscar administraciones por texto
   * @param {String} searchText - Texto a buscar
   */
  const buscar = async (searchText) => {
    if (!searchText || searchText.trim() === '') {
      return listar()
    }

    loading.value = true
    error.value = null

    // Añadir % para búsqueda con ilike
    const searchPattern = `%${searchText}%`

    try {
      const { onResult, onError } = useQuery(
        queries.BUSCAR_ADMINISTRACIONES,
        {
          search: searchPattern,
          limit: limit.value
        },
        {
          fetchPolicy: 'network-only'
        }
      )

      return new Promise((resolve, reject) => {
        onResult(({ data }) => {
          items.value = data?.administraciones || []
          loading.value = false
          resolve(items.value)
        })

        onError((err) => {
          error.value = `Error en búsqueda: ${err.message}`
          loading.value = false
          reject(err)
        })
      })
    } catch (err) {
      error.value = `Error en búsqueda: ${err.message}`
      loading.value = false
      throw err
    }
  }

  /**
   * Listar por ámbito
   * @param {String} ambito - ESTATAL, AUTONOMICO, LOCAL, etc.
   */
  const listarPorAmbito = async (ambito) => {
    return listar({ ambito: { eq: ambito } })
  }

  /**
   * Listar por municipio
   * @param {String} municipioId - UUID del municipio
   */
  const listarPorMunicipio = async (municipioId) => {
    return listar({ municipioId: { eq: municipioId } })
  }

  /**
   * Crear nueva administración
   * @param {Object} inputData - Datos de la administración
   */
  const crear = async (inputData) => {
    loading.value = true
    error.value = null

    try {
      const { mutate } = useMutation(queries.CREAR_ADMINISTRACION)
      const { data, errors } = await mutate({ data: inputData })

      if (errors && errors.length > 0) {
        throw new Error(errors[0].message)
      }

      const nuevoItem = data.createAdministracion

      // Añadir al inicio de la lista
      items.value.unshift(nuevoItem)

      loading.value = false
      return nuevoItem
    } catch (err) {
      error.value = `Error al crear administración: ${err.message}`
      console.error('Error en crear administración:', err)
      loading.value = false
      throw err
    }
  }

  /**
   * Actualizar administración existente
   * @param {String} id - UUID de la administración
   * @param {Object} inputData - Datos a actualizar
   */
  const actualizar = async (id, inputData) => {
    loading.value = true
    error.value = null

    try {
      const { mutate } = useMutation(queries.ACTUALIZAR_ADMINISTRACION)
      const { data, errors } = await mutate({
        data: {
          id,
          ...inputData
        }
      })

      if (errors && errors.length > 0) {
        throw new Error(errors[0].message)
      }

      const itemActualizado = data.updateAdministracion

      // Actualizar en la lista
      const index = items.value.findIndex(i => i.id === id)
      if (index !== -1) {
        items.value[index] = itemActualizado
      }

      // Actualizar item individual si es el que estamos viendo
      if (item.value?.id === id) {
        item.value = itemActualizado
      }

      loading.value = false
      return itemActualizado
    } catch (err) {
      error.value = `Error al actualizar administración: ${err.message}`
      console.error('Error en actualizar administración:', err)
      loading.value = false
      throw err
    }
  }

  /**
   * Eliminar administración
   * @param {String} id - UUID de la administración
   */
  const eliminar = async (id) => {
    loading.value = true
    error.value = null

    try {
      const { mutate } = useMutation(queries.ELIMINAR_ADMINISTRACION)
      const { data, errors } = await mutate({ id })

      if (errors && errors.length > 0) {
        throw new Error(errors[0].message)
      }

      // Eliminar de la lista
      items.value = items.value.filter(i => i.id !== id)

      // Limpiar item si es el que eliminamos
      if (item.value?.id === id) {
        item.value = null
      }

      loading.value = false
      return data.deleteAdministraciones
    } catch (err) {
      error.value = `Error al eliminar administración: ${err.message}`
      console.error('Error en eliminar administración:', err)
      loading.value = false
      throw err
    }
  }

  /**
   * Cargar siguiente página (paginación infinita)
   */
  const cargarMas = async () => {
    if (!hasMore.value || loading.value) {
      return
    }

    offset.value += limit.value
    return listar(activeFilters.value, true)
  }

  /**
   * Resetear estado
   */
  const reset = () => {
    items.value = []
    item.value = null
    error.value = null
    loading.value = false
    offset.value = 0
    hasMore.value = true
    activeFilters.value = {}
  }

  /**
   * Cambiar el límite de resultados
   * @param {Number} newLimit - Nuevo límite
   */
  const cambiarLimite = (newLimit) => {
    limit.value = newLimit
    offset.value = 0
  }

  return {
    // Estado
    items,
    item,
    loading,
    error,
    offset,
    limit,
    hasMore,
    activeFilters,

    // Computed
    hasItems,
    isEmpty,
    totalCargados,

    // Métodos
    listar,
    obtener,
    buscar,
    listarPorAmbito,
    listarPorMunicipio,
    crear,
    actualizar,
    eliminar,
    cargarMas,
    reset,
    cambiarLimite
  }
}