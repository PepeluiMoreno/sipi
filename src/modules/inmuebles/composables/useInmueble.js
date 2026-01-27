import { computed } from 'vue'
import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/inmuebleQueries.js'

export function useInmueble() {
  // 'inmuebles' es el nombre de la query raiz en GraphQL
  const base = useAgenteBase('inmuebles', queries)

  const inmuebles = computed(() => base.items.value)
  const inmueble = computed(() => base.item.value)

  /**
   * Listar con mapeo de filtros de UI a Strawchemy
   * @param {Object} filters - Filtros de la UI (search, provinciaId, municipioId, estados)
   * @param {Boolean} append - Si es true, añade a los items existentes
   */
  const listar = async (filters = {}, append = false) => {
    const strawchemyFilter = {}
    const andConditions = []

    // Búsqueda textual
    if (filters.search && filters.search.trim()) {
      andConditions.push({
        _or: [
          { nombre: { ilike: `%${filters.search}%` } },
          { direccion: { ilike: `%${filters.search}%` } }
        ]
      })
    }

    // Filtro por municipio (más específico que provincia)
    if (filters.municipioId) {
      andConditions.push({ municipioId: { eq: filters.municipioId } })
    }
    // Si solo hay provincia, filtrar por municipios de esa provincia
    // Nota: esto requiere que el backend soporte filtro nested o lo manejamos diferente
    // Por ahora, si hay provinciaId sin municipioId, no filtramos geográficamente
    // ya que el usuario debe seleccionar un municipio específico

    // Combinar condiciones con _and
    if (andConditions.length > 0) {
      if (andConditions.length === 1) {
        Object.assign(strawchemyFilter, andConditions[0])
      } else {
        strawchemyFilter._and = andConditions
      }
    }

    return base.listar(strawchemyFilter, append)
  }

  return {
    ...base,
    inmuebles,
    inmueble,
    // Override listar to add custom mapping if needed
    listar
  }
}