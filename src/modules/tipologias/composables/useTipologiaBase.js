import { ref, computed } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'

export function useTipologiaBase(catalogoNombre, options = {}) {
  const { conContacto = false } = options
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({ page: 1, pageSize: 50, total: 0 })

  // Obtener el cliente Apollo durante el setup del composable
  const { resolveClient } = useApolloClient()
  const getClient = () => resolveClient()

  // Import dinámico pero con import() en lugar de require()
  const loadQueries = async () => {
    const module = await import(`../graphql/${catalogoNombre}Queries.js`)
    return module
  }

  const listar = async (filter = {}, options = {}) => {
    loading.value = true
    error.value = null

    try {
      const queries = await loadQueries()
      const { LISTAR } = queries

      // Usar el cliente Apollo directamente
      const client = getClient()

      // Permitir pasar limit personalizado o null para sin límite
      const limit = options.limit !== undefined ? options.limit : pagination.value.pageSize
      const offset = options.offset !== undefined ? options.offset : (pagination.value.page - 1) * pagination.value.pageSize

      const variables = {
        filter
      }

      // Solo agregar limit y offset si limit no es null
      if (limit !== null) {
        variables.limit = limit
        variables.offset = offset
      }

      const { data } = await client.query({
        query: LISTAR,
        variables,
        fetchPolicy: 'cache-first' // Usar caché de Apollo primero
      })

      const response = data?.[catalogoNombre]
      items.value = response || []

      // Sin paginación total del servidor, asumimos que si vienen menos que el límite, es la última página
      if (limit !== null) {
        pagination.value.total = items.value.length < limit
          ? offset + items.value.length
          : offset + items.value.length + 1
      } else {
        pagination.value.total = items.value.length
      }

      return { items: items.value, total: pagination.value.total }
    } catch (err) {
      error.value = `Error al cargar ${catalogoNombre}: ${err.message}`
      console.error(`Error en listar ${catalogoNombre}:`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    loading,
    error,
    pagination,
    listar
  }
}