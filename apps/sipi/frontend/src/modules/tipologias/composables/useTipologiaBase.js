import { ref } from 'vue'
import { gql } from '@apollo/client/core'
import { useApolloClient } from '@vue/apollo-composable'

/**
 * Composable base para catálogos/tipologías.
 *
 * La API GraphQL es genérica y homogénea para todas las entidades:
 *   <catalogo>(limit: Int!, offset: Int!, search: String, filters: [FilterInput!]) {
 *     items { id nombre } total
 *   }
 *
 * Por eso ya NO dependemos de un fichero de queries por catálogo (muchos estaban
 * desfasados con la forma antigua de Strawchemy: `$filter: XFilterInput` y selección
 * de campos directamente sobre la lista). Construimos la query dinámicamente: para un
 * desplegable solo necesitamos `id` y `nombre`.
 *
 * @param {String} catalogoNombre  Nombre del campo de lista en GraphQL (p.ej. 'tiposEntidadReligiosa')
 */
export function useTipologiaBase(catalogoNombre /*, options = {} */) {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({ page: 1, pageSize: 500, total: 0 })

  const { resolveClient } = useApolloClient()
  const getClient = () => resolveClient()

  const LISTAR = gql`
    query ListarCatalogo($limit: Int!, $offset: Int!, $search: String) {
      ${catalogoNombre}(limit: $limit, offset: $offset, search: $search) {
        items { id nombre }
        total
      }
    }
  `

  /**
   * @param {Object} _filter  (ignorado — compatibilidad de firma)
   * @param {Object} options  { limit, offset, search }
   */
  const listar = async (_filter = {}, options = {}) => {
    loading.value = true
    error.value = null
    try {
      const client = getClient()
      const limit = options.limit ?? pagination.value.pageSize
      const offset = options.offset ?? 0
      const search = typeof options.search === 'string' && options.search.trim()
        ? options.search.trim()
        : null

      const { data } = await client.query({
        query: LISTAR,
        variables: { limit, offset, search },
        fetchPolicy: 'cache-first'
      })

      const conexion = data?.[catalogoNombre] || {}
      items.value = conexion.items || []
      pagination.value.total = conexion.total ?? items.value.length

      return { items: items.value, total: pagination.value.total }
    } catch (err) {
      error.value = `Error al cargar ${catalogoNombre}: ${err.message}`
      console.error(`Error en listar ${catalogoNombre}:`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, pagination, listar }
}
