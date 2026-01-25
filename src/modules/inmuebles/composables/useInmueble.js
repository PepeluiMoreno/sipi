import { computed } from 'vue'
import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/inmuebleQueries.js'

export function useInmueble() {
  // 'inmuebles' es el nombre de la query raiz en GraphQL
  const base = useAgenteBase('inmuebles', queries)

  const inmuebles = computed(() => base.items.value)
  const inmueble = computed(() => base.item.value)

  /**
   * Listar con mapeo de filtros antiguos a Strawchemy si es necesario
   * O simplemente pasar los filtros directos.
   * Por ahora asumimos que la UI pasará filtros compatibles o mapeados aquí.
   */
  const listar = async (filters = {}, append = false) => {
    // Aquí podríamos transformar filtros de UI a Strawchemy
    // Ejemplo: 'search' simple a _or complex
    // Pero useAgenteBase ya maneja 'buscar' con search text
    // Si filters trae 'search', usamos base.buscar? No, base.buscar es otro metodo.

    // Si filters es complex object de Strawchemy, lo pasamos directo.
    // Si es un objeto simple legacy, hacemos map.

    // Mapeo básico de legacy a Strawchemy
    const strawchemyFilter = { ...filters }

    // Si hay 'search' y no es el campo search de query, sino filtro local
    if (filters.search && !filters._or) {
      // El backend espera 'search' en query root BUSCAR, o filtro manual en LISTAR
      // Si usamos LISTAR y queremos buscar textualmente:
      delete strawchemyFilter.search
      strawchemyFilter._or = [
        { nombre: { ilike: `%${filters.search}%` } },
        { direccion: { ilike: `%${filters.search}%` } }
      ]
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