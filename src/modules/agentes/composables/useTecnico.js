import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/tecnicoQueries.strawchemy'

export function useTecnico() {
  const base = useAgenteBaseStrawchemy('tecnicos', queries)

  // Alias para mantener compatibilidad
  const tecnicos = computed(() => base.items.value)
  const tecnico = computed(() => base.item.value)
  const pagination = computed(() => ({
    page: 1,
    pageSize: base.limit.value,
    total: base.totalCargados.value
  }))

  /**
   * Listar con filtros específicos de técnicos
   * @param {Object} filters - Filtros (rolTecnicoId, colegioProfesionalId, municipioId, etc.)
   */
  const listar = async (filters = {}) => {
    const strawchemyFilters = {}

    if (filters.search) {
      strawchemyFilters._or = [
        { nombre: { ilike: `%${filters.search}%` } },
        { razonSocial: { ilike: `%${filters.search}%` } },
        { numeroIdentificacion: { contains: filters.search } }
      ]
    }

    if (filters.rolTecnicoId) {
      strawchemyFilters.rolTecnicoId = { eq: filters.rolTecnicoId }
    }

    if (filters.colegioProfesionalId) {
      strawchemyFilters.colegioProfesionalId = { eq: filters.colegioProfesionalId }
    }

    if (filters.municipioId) {
      strawchemyFilters.municipioId = { eq: filters.municipioId }
    }

    return base.listar(strawchemyFilters)
  }

  const listarPorMunicipio = async (municipioId) => {
    return base.listar({ municipioId: { eq: municipioId } })
  }

  const listarPorRol = async (rolTecnicoId) => {
    return base.listar({ rolTecnicoId: { eq: rolTecnicoId } })
  }

  const listarPorColegio = async (colegioProfesionalId) => {
    return base.listar({ colegioProfesionalId: { eq: colegioProfesionalId } })
  }

  return {
    // Estado con aliases
    tecnicos,
    tecnico,
    loading: base.loading,
    error: base.error,
    pagination,

    // Métodos personalizados
    listar,
    listarPorMunicipio,
    listarPorRol,
    listarPorColegio,

    // Métodos del base
    obtener: base.obtener,
    buscar: base.buscar,
    crear: base.crear,
    actualizar: base.actualizar,
    eliminar: base.eliminar,
    cargarMas: base.cargarMas,
    reset: base.reset
  }
}
