import { useAgenteBase } from '../../agentes/composables/useAgenteBase'

/**
 * Wrapper para Tipologías
 * @param {String} pluralName Nombre de la entidad en plural (como viene en la respuesta GraphQL)
 * @param {Object} queries Objeto con las queries (LISTAR, OBTENER, CREAR, ACTUALIZAR, ELIMINAR)
 */
export function useTipologiaBaseStrawchemy(pluralName, queries) {
    // Simplemente delegamos en el composable genérico de agentes
    // ya que la lógica es idéntica (CRUD simple + paginación/filtros)
    const base = useAgenteBase(pluralName, queries)

    return {
        ...base
        // Podríamos añadir lógica específica de tipologías aquí si fuera necesario
    }
}
