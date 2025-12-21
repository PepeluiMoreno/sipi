import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from './useAgenteBaseStrawchemy'
import * as queries from '../graphql/tecnicoQueries.js'

/**
 * Composable para Técnicos
 * Reutiliza la lógica base de Strawchemy
 */
export function useTecnico() {
  // 'tecnicos' es el nombre de la query raiz en GraphQL (schema.py: tecnicos: list[TecnicoType])
  const base = useAgenteBaseStrawchemy('tecnicos', queries)

  // Alias para mantener compatibilidad con componentes existentes
  const tecnicos = computed(() => base.items.value)
  const tecnico = computed(() => base.item.value)

  // Exponer métodos específicos si hacen falta
  const listarPorMunicipio = async (municipioId) => {
    // Usamos el listado genérico filtrando
    return base.listar({ municipioId: { eq: municipioId } })
  }

  return {
    ...base,
    // Alias extras
    tecnicos,
    tecnico,
    // Métodos específicos
    listarPorMunicipio
  }
}
