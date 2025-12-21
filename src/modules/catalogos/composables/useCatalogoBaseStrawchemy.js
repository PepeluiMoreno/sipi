import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'

/**
 * Wrapper para Catálogos usando Strawchemy
 * @param {String} pluralName Nombre de la entidad en plural (como viene en la respuesta GraphQL)
 * @param {Object} queries Objeto con las queries (LISTAR, OBTENER, CREAR, ACTUALIZAR, ELIMINAR)
 */
export function useCatalogoBaseStrawchemy(pluralName, queries) {
    // Simplemente delegamos en el composable genérico de agentes
    // ya que la lógica es idéntica (CRUD simple + paginación/filtros)
    const base = useAgenteBaseStrawchemy(pluralName, queries)

    return {
        ...base
        // Podríamos añadir lógica específica de catálogos aquí si fuera necesario
    }
}
