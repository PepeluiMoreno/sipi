import { ref, computed } from 'vue'
import { useApolloClient, useMutation } from '@vue/apollo-composable'

/**
 * Composable base genérico para agentes adaptado a Strawchemy
 * 
 * @param {String} entityName - Nombre de la entidad en GraphQL (ej: 'notarias', 'administraciones')
 * @param {Object} queries - Objeto con las queries/mutations importadas
 * @param {Object} options - Opciones de configuración
 * @returns {Object} Objeto con estado y métodos del composable
 * 
 * Cambios principales respecto a useAgenteBase:
 * - Paginación con offset/limit en vez de page/pageSize
 * - Filtros avanzados usando operadores de Strawchemy (eq, ilike, contains, _or, _and)
 * - Sin wrapping de respuestas (acceso directo al array)
 * - Soporte para agregaciones automáticas
 * - Infinite scroll en vez de paginación tradicional
 */
export function useAgenteBase(entityName, queries, options = {}) {
    const {
        limit: defaultLimit = 50,
        fetchPolicy = 'network-only'
    } = options

    // Estado
    const items = ref([])
    const item = ref(null)
    const loading = ref(false)
    const error = ref(null)

    // Paginación offset-based
    const offset = ref(0)
    const limit = ref(defaultLimit)
    const hasMore = ref(true)

    // Filtros activos (guardados para cargarMas)
    const activeFilters = ref({})

    // Obtener el cliente Apollo durante el setup del composable
    const { resolveClient } = useApolloClient()
    const getClient = () => resolveClient()

    // Computed
    const hasItems = computed(() => items.value.length > 0)
    const isEmpty = computed(() => !loading.value && items.value.length === 0)
    const totalCargados = computed(() => items.value.length)

    /**
     * Listar entidades con filtros
     * @param {Object} filters - Filtros de Strawchemy (ej: { nombre: { ilike: "%texto%" } })
     * @param {Boolean} append - Si es true, añade a los items existentes (para paginación infinita)
     */
    const listar = async (filters = {}, append = false) => {
        loading.value = true
        error.value = null

        try {
            const client = getClient()

            const variables = { offset: append ? offset.value : 0, limit: limit.value }

            // Traducción del objeto de filtros del UI → API genérica:
            //   search → arg `search` (ILIKE sobre nombre, lo resuelve el servidor)
            //   array  → { field, operator: IN, values }
            //   escalar→ { field, operator: EQ, value }
            const fl = []
            for (const [campo, valor] of Object.entries(filters || {})) {
                if (campo === 'search') {
                    if (typeof valor === 'string' && valor.trim()) variables.search = valor.trim()
                    continue
                }
                if (valor === null || valor === undefined || valor === '') continue
                if (Array.isArray(valor)) {
                    if (valor.length) fl.push({ field: campo, operator: 'IN', values: valor.map(String) })
                    continue
                }
                fl.push({ field: campo, operator: 'EQ', value: String(valor) })
            }
            if (fl.length) variables.filters = fl

            const { data } = await client.query({
                query: queries.LISTAR,
                variables,
                fetchPolicy
            })

            // API genérica: { items, total }
            const conexion = data?.[entityName] || {}
            const resultados = conexion.items || []

            if (append) {
                items.value = [...items.value, ...resultados]
            } else {
                items.value = resultados
                offset.value = 0
            }

            hasMore.value = resultados.length === limit.value
            activeFilters.value = filters

            loading.value = false
            return { items: items.value, total: conexion.total ?? items.value.length }
        } catch (err) {
            error.value = `Error al cargar ${entityName}: ${err.message}`
            console.error(`Error en listar ${entityName}:`, err)
            loading.value = false
            throw err
        }
    }

    /**
     * Obtener una entidad por ID
     * @param {String} id - UUID de la entidad
     */
    const obtener = async (id) => {
        loading.value = true
        error.value = null

        try {
            const client = getClient()

            const { data } = await client.query({
                query: queries.OBTENER,
                variables: {
                    filter: { id: { eq: id } }
                },
                fetchPolicy
            })

            const resultados = data?.[entityName] || []
            item.value = resultados.length > 0 ? resultados[0] : null
            loading.value = false
            return item.value
        } catch (err) {
            error.value = `Error al obtener ${entityName}: ${err.message}`
            console.error(`Error al obtener ${entityName}:`, err)
            loading.value = false
            throw err
        }
    }

    /**
     * Buscar entidades por texto (si existe la query BUSCAR)
     * @param {String} searchText - Texto a buscar
     */
    const buscar = async (searchText) => {
        if (!queries.BUSCAR) {
            console.warn(`BUSCAR query no disponible para ${entityName}`)
            return listar()
        }

        if (!searchText || searchText.trim() === '') {
            return listar()
        }

        loading.value = true
        error.value = null

        // Añadir % para búsqueda con ilike
        const searchPattern = `%${searchText}%`

        try {
            const client = getClient()

            const { data } = await client.query({
                query: queries.BUSCAR,
                variables: {
                    search: searchPattern,
                    limit: limit.value
                },
                fetchPolicy
            })

            items.value = data?.[entityName] || []
            loading.value = false
            return items.value
        } catch (err) {
            error.value = `Error en búsqueda: ${err.message}`
            console.error(`Error en búsqueda ${entityName}:`, err)
            loading.value = false
            throw err
        }
    }

    /**
     * Crear nueva entidad
     * @param {Object} inputData - Datos de la entidad
     */
    const crear = async (inputData) => {
        loading.value = true
        error.value = null

        try {
            const { mutate } = useMutation(queries.CREAR)
            const { data, errors } = await mutate({ data: inputData })

            if (errors && errors.length > 0) {
                throw new Error(errors[0].message)
            }

            // El nombre de la mutation puede variar, obtener el primer key
            const mutationKey = Object.keys(data)[0]
            const nuevoItem = data[mutationKey]

            // Añadir al inicio de la lista
            items.value.unshift(nuevoItem)

            loading.value = false
            return nuevoItem
        } catch (err) {
            error.value = `Error al crear ${entityName}: ${err.message}`
            console.error(`Error en crear ${entityName}:`, err)
            loading.value = false
            throw err
        }
    }

    /**
     * Actualizar entidad existente
     * @param {String} id - UUID de la entidad
     * @param {Object} inputData - Datos a actualizar
     */
    const actualizar = async (id, inputData) => {
        loading.value = true
        error.value = null

        try {
            const { mutate } = useMutation(queries.ACTUALIZAR)
            const { data, errors } = await mutate({
                data: {
                    id,
                    ...inputData
                }
            })

            if (errors && errors.length > 0) {
                throw new Error(errors[0].message)
            }

            // El nombre de la mutation puede variar, obtener el primer key
            const mutationKey = Object.keys(data)[0]
            const itemActualizado = data[mutationKey]

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
            error.value = `Error al actualizar ${entityName}: ${err.message}`
            console.error(`Error en actualizar ${entityName}:`, err)
            loading.value = false
            throw err
        }
    }

    /**
     * Eliminar entidad
     * @param {String} id - UUID de la entidad
     */
    const eliminar = async (id) => {
        loading.value = true
        error.value = null

        try {
            const { mutate } = useMutation(queries.ELIMINAR)
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
            const mutationKey = Object.keys(data)[0]
            return data[mutationKey]
        } catch (err) {
            error.value = `Error al eliminar ${entityName}: ${err.message}`
            console.error(`Error en eliminar ${entityName}:`, err)
            loading.value = false
            throw err
        }
    }

    /**
     * Purgar (borrado físico permanente). Requiere queries.PURGAR; si no, hace soft-delete.
     * @param {String} id - UUID de la entidad
     */
    const purgar = async (id) => {
        if (!queries.PURGAR) return eliminar(id)
        loading.value = true
        error.value = null
        try {
            const { mutate } = useMutation(queries.PURGAR)
            const { data, errors } = await mutate({ id })
            if (errors && errors.length > 0) {
                throw new Error(errors[0].message)
            }
            items.value = items.value.filter(i => i.id !== id)
            if (item.value?.id === id) item.value = null
            loading.value = false
            return data
        } catch (err) {
            error.value = `Error al purgar ${entityName}: ${err.message}`
            console.error(`Error en purgar ${entityName}:`, err)
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
        crear,
        actualizar,
        eliminar,
        purgar,
        cargarMas,
        reset,
        cambiarLimite
    }
}
